import React, { createContext, useContext, useCallback, useState } from "react";
import { Comment, getCommentsApi } from "../services/commentService";

type CommentActionType = "CREATE" | "EDIT" | "DELETE";

interface CommentContextType {
  triggerRefresh: (type: CommentActionType) => void;
  comments: Comment[];
  isLoading: boolean;
}

const CommentContext = createContext<CommentContextType | undefined>(undefined);

export const useCommentContext = () => {
  const context = useContext(CommentContext);
  if (!context) {
    throw new Error("useCommentContext must be used within a CommentProvider");
  }
  return context;
};

interface CommentProviderProps {
  children: React.ReactNode;
  postId: number;
  onCommentCreate: () => void;
}

export const CommentProvider: React.FC<CommentProviderProps> = ({
  children,
  postId,
  onCommentCreate,
}) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchComments = useCallback(async () => {
    try {
      setIsLoading(true);
      const newComments = await getCommentsApi(postId);
      setComments(newComments);
    } catch (error) {
      console.error("Failed to fetch comments:", error);
    } finally {
      setIsLoading(false);
    }
  }, [postId]);

  const triggerRefresh = useCallback(
    async (type: CommentActionType) => {
      switch (type) {
        case "CREATE":
          // When creating a comment, refresh both post and comment list
          onCommentCreate();
          await fetchComments();
          break;
        case "EDIT":
        case "DELETE":
          // When editing or deleting, only refresh comment list
          await fetchComments();
          break;
      }
    },
    [onCommentCreate, fetchComments]
  );

  // Initial fetch
  React.useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  return (
    <CommentContext.Provider value={{ triggerRefresh, comments, isLoading }}>
      {children}
    </CommentContext.Provider>
  );
};
