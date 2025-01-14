import React, { useState } from "react";
import { Comment as CommentType } from "../../services/commentService";
import { useCommentContext } from "../../contexts/CommentContext";
import { useAuth } from "../../contexts/AuthContext";
import {
  deleteCommentApi,
  editCommentApi,
} from "../../services/commentService";

interface CommentProps {
  comment: CommentType;
}

export const Comment: React.FC<CommentProps> = ({ comment }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const { triggerRefresh } = useCommentContext();
  const { user } = useAuth();

  const isCommentAuthor = user?.username === comment.created_by;

  const handleEdit = async () => {
    try {
      await editCommentApi(comment.id, editContent, () => {
        triggerRefresh("EDIT");
        setIsEditing(false);
      });
    } catch (error) {
      console.error("Failed to edit comment:", error);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteCommentApi(comment.id, () => {
        triggerRefresh("DELETE");
      });
    } catch (error) {
      console.error("Failed to delete comment:", error);
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <div className="flex justify-between items-start">
        <div>
          <div className="font-medium text-gray-900">{comment.created_by}</div>
          <div className="text-sm text-gray-500">{comment.created_at}</div>
        </div>
        {isCommentAuthor && (
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <button
                  className="text-sm text-gray-600 hover:text-gray-800"
                  onClick={() => setIsEditing(false)}
                >
                  Cancel
                </button>
                <button
                  className="text-sm text-blue-600 hover:text-blue-800"
                  onClick={handleEdit}
                >
                  Save
                </button>
              </>
            ) : (
              <>
                <button
                  className="text-sm text-gray-600 hover:text-gray-800"
                  onClick={() => setIsEditing(true)}
                >
                  Edit
                </button>
                <button
                  className="text-sm text-red-600 hover:text-red-800"
                  onClick={handleDelete}
                >
                  Delete
                </button>
              </>
            )}
          </div>
        )}
      </div>
      {isEditing ? (
        <textarea
          className="w-full p-2 mt-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          value={editContent}
          onChange={(e) => setEditContent(e.target.value)}
          rows={3}
        />
      ) : (
        <p className="mt-2 text-gray-700">{comment.content}</p>
      )}
    </div>
  );
};
