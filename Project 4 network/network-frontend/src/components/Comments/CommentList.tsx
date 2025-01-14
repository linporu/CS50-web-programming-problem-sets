import React from "react";
import { useCommentContext } from "../../contexts/CommentContext";
import { Comment as CommentComponent } from "./Comment";

export const CommentList: React.FC = () => {
  const { comments, isLoading } = useCommentContext();

  if (isLoading) {
    return <div className="animate-pulse">Loading comments...</div>;
  }

  return (
    <div className="space-y-4">
      {comments.map((comment) => (
        <CommentComponent key={comment.id} comment={comment} />
      ))}
    </div>
  );
};
