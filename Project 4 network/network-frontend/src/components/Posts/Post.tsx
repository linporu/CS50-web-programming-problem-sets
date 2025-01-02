import { useAuth } from "@/contexts/AuthContext";
import { editPostApi, deletePostApi } from "@/services/postService";
import { useState } from "react";

interface PostProps {
  id: number;
  content: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  likes_count: number;
  comments_count: number;
  comments: {
    id: number;
    content: string;
    created_by: string;
    created_at: string;
    is_deleted: boolean;
  }[];
  onPostUpdate?: () => void;
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
      onPostUpdate?.();
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

  return (
    <div className="rounded-lg border border-gray-200 p-4 shadow-sm">
      {/* Post Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {/* 可以之後加入用戶頭像 */}
          <span className="font-medium">{created_by}</span>
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
        <button className="flex items-center gap-1 hover:text-blue-500">
          <span>Like</span>
          <span>{likes_count}</span>
        </button>

        <button className="flex items-center gap-1 hover:text-blue-500">
          <span>Comment</span>
          <span>{comments_count}</span>
        </button>
      </div>
    </div>
  );
}
