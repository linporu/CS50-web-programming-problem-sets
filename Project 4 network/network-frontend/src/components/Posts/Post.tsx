import { useAuth } from "@/contexts/AuthContext";
import { editPostApi, deletePostApi, getPostApi } from "@/services/postService";
import { useState } from "react";
import { Link } from "react-router-dom";
import LikeButton from "../Buttons/LikeButton";
import { CreateComment } from "../Comments/CreateComment";
import { CommentList } from "../Comments/CommentList";
import { CommentProvider } from "@/contexts/CommentContext";

interface PostProps {
  id: number;
  content: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  likes_count: number;
  comments_count: number;
  onPostUpdate?: () => void;
  is_liked: boolean;
}

export default function Post({
  id,
  content,
  created_by,
  created_at,
  updated_at,
  likes_count,
  comments_count,
  onPostUpdate,
}: PostProps) {
  // Add states for editing
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(content);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();
  const isPostCreator = user?.username === created_by;
  const [currentLikesCount, setCurrentLikesCount] = useState(likes_count);
  const [isLiked, setIsLiked] = useState(false);
  const [currentCommentsCount, setCurrentCommentsCount] =
    useState(comments_count);

  // Handle edit mode
  const handleEditClick = () => {
    setIsEditing(true);
    setEditContent(content);
  };

  // Handle save edit
  const handleSaveEdit = async () => {
    if (!editContent.trim()) {
      setError("Content cannot be empty");
      return;
    }

    if (editContent === content) {
      setError("No changes were made to the post content");
      return;
    }

    try {
      await editPostApi(id, editContent);
      setError(null);
      await updatePost(id);
    } catch (error) {
      console.error("Failed to update post:", error);
      setError(
        `Failed to update post: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    } finally {
      setIsEditing(false);
    }
  };

  // Handle cancel edit
  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditContent(content);
    return;
  };

  const handleDeleteClick = async () => {
    try {
      await deletePostApi(id);
      setError(null);
      onPostUpdate?.();
    } catch (error) {
      console.error("Failed to delete post:", error);
      setError(
        `Failed to delete post: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    }
    return;
  };

  const updatePost = async (postId: number) => {
    try {
      const updatedPost = await getPostApi(postId);
      setCurrentLikesCount(updatedPost.likes_count);
      setCurrentCommentsCount(updatedPost.comments_count);
      setIsLiked(updatedPost.is_liked);
      onPostUpdate?.();
    } catch (error) {
      console.error("Failed to fetch updated post:", error);
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 p-4 shadow-sm">
      {/* Post Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {/* 可以之後加入用戶頭像 */}
          <Link
            to={`/profile/${created_by}`}
            className="font-medium hover:text-blue-500 hover:underline"
          >
            {created_by}
          </Link>
          <span className="text-sm text-gray-500">
            {updated_at ? updated_at : created_at}
          </span>
        </div>
        {isPostCreator && !isEditing && (
          <div className="flex gap-2">
            <button
              className="text-sm text-gray-600 hover:text-blue-500"
              onClick={handleEditClick}
            >
              Edit
            </button>
            <button
              className="text-sm text-gray-600 hover:text-blue-500"
              onClick={handleDeleteClick}
            >
              Delete
            </button>
          </div>
        )}
      </div>

      {/* Post Content */}
      {error && <div className="mb-2 text-sm text-red-500">{error}</div>}
      {isEditing ? (
        <div className="mb-4">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={4}
            data-testid="post-edit-textarea"
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleSaveEdit}
              className="px-3 py-1 text-sm text-white bg-blue-500 rounded hover:bg-blue-600"
            >
              Save
            </button>
            <button
              onClick={handleCancelEdit}
              className="px-3 py-1 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-100"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <p className="mb-4">{content}</p>
      )}

      {/* Post Footer */}
      <div className="flex items-center gap-4 text-sm text-gray-600">
        <LikeButton
          postId={id}
          initialIsLiked={isLiked}
          likesCount={currentLikesCount}
          onLikeUpdate={() => {
            updatePost(id);
          }}
        />

        <div className="flex items-center gap-1 text-gray-600">
          <span>Comments</span>
          <span>{currentCommentsCount}</span>
        </div>
      </div>

      {/* Comments Section */}
      <div className="mt-4 border-t pt-4">
        <CommentProvider
          postId={id}
          onCommentCreate={() => {
            updatePost(id);
          }}
        >
          {user && <CreateComment postId={id} />}
          <CommentList />
        </CommentProvider>
      </div>
    </div>
  );
}
