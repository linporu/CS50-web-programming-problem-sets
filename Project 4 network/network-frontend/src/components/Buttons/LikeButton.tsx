import { useState } from "react";
import { likePostApi, unLikePostApi } from "../../services/postService";

export default function LikeButton({
  postId,
  initialIsLiked,
  likesCount,
  onLikeUpdate,
}: {
  postId: number;
  initialIsLiked: boolean;
  likesCount: number;
  onLikeUpdate: (newLikesCount: number, isLiked: boolean) => void;
}) {
  const [isLiked, setIsLiked] = useState(initialIsLiked);
  const [currentLikesCount, setCurrentLikesCount] = useState(likesCount);
  const [isLoading, setIsLoading] = useState(false);

  const handleLikeToggle = async () => {
    setIsLoading(true);
    try {
      if (isLiked) {
        await unLikePostApi(postId);
        setCurrentLikesCount((prev) => prev - 1);
      } else {
        await likePostApi(postId);
        setCurrentLikesCount((prev) => prev + 1);
      }
      setIsLiked(!isLiked);
      onLikeUpdate(currentLikesCount, !isLiked);
    } catch (error) {
      console.error("Like action failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleLikeToggle}
      disabled={isLoading}
      className={`flex items-center gap-1 ${
        isLiked ? "text-blue-500" : "text-gray-600"
      } hover:text-blue-500`}
    >
      {isLoading ? (
        <span>Loading...</span>
      ) : (
        <>
          <span>{isLiked ? "Unlike" : "Like"}</span>
          <span>{currentLikesCount}</span>
        </>
      )}
    </button>
  );
}
