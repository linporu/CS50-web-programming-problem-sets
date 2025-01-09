import { useState } from "react";
import {
  followUserApi,
  unfollowUserApi,
  UserProfile,
} from "../../services/userService";

export default function FollowButton({
  targetUser,
  onFollowingUpdate = () => {},
}: {
  targetUser: UserProfile;
  onFollowingUpdate?: () => void;
}) {
  const [isFollowing, setIsFollowing] = useState(targetUser.is_following);
  const [isLoading, setIsLoading] = useState(false);
  const username = targetUser.username;

  const handleFollowToggle = async () => {
    setIsLoading(true);
    try {
      if (isFollowing) {
        await unfollowUserApi(username);
      } else {
        await followUserApi(username);
      }
      setIsFollowing(!isFollowing);
      onFollowingUpdate();
    } catch (error) {
      console.error("Follow action failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleFollowToggle}
      disabled={isLoading}
      className={`px-4 py-2 rounded ${
        isFollowing
          ? "bg-gray-200 hover:bg-red-500 hover:text-white"
          : "bg-blue-500 text-white hover:bg-blue-600"
      }`}
    >
      {isLoading ? (
        <span>Loading...</span>
      ) : isFollowing ? (
        "Unfollow"
      ) : (
        "Follow"
      )}
    </button>
  );
}
