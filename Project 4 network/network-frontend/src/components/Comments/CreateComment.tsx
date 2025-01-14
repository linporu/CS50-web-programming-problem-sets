import React, { useState } from "react";
import { createCommentApi } from "../../services/commentService";
import { useCommentContext } from "../../contexts/CommentContext";

interface CreateCommentProps {
  postId: number;
  onCommentCreated?: () => void;
}

export const CreateComment: React.FC<CreateCommentProps> = ({
  postId,
  onCommentCreated,
}) => {
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { triggerRefresh } = useCommentContext();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!content.trim()) {
      setError("Comment cannot be empty");
      return;
    }

    try {
      await createCommentApi(postId, content, () => {
        triggerRefresh("CREATE");
        onCommentCreated?.();
      });
      setContent("");
      setError(null);
    } catch (error) {
      console.error("Failed to create comment:", error);
      setError(
        `Failed to create comment: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mb-4">
      {error && <div className="text-sm text-red-500 mb-2">{error}</div>}
      <div className="flex gap-2">
        <textarea
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            setError(null);
          }}
          placeholder="Write a comment..."
          className="flex-1 p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={2}
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 self-start"
        >
          Comment
        </button>
      </div>
    </form>
  );
};
