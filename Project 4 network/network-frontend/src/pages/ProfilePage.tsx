import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import PostList from "../components/Posts/PostList";
import { getUserProfileApi, UserProfile } from "../services/userService";

export default function ProfilePage() {
  const { username } = useParams<{ username: string }>();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      if (!username) return;
      try {
        const data = await getUserProfileApi(username);
        setProfile(data);
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, [username]);

  if (!username || isLoading) return null;

  return (
    <div className="container mx-auto px-4">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">{profile?.username}</h2>
        <div className="mt-2 text-gray-600">
          <span className="mr-4">Followers: {profile?.follower_count}</span>
          <span>Following: {profile?.following_count}</span>
        </div>
      </div>
      <PostList mode="user" username={username} />
    </div>
  );
}
