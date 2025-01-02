import { useEffect, useState, useCallback } from "react";
import Post from "./Post";
import { getPostApi, getFollowingPostApi } from "../../services/postService";
import { CreatePost } from "./CreatePost";

type Post = {
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
};

interface PostListProps {
  mode?: "all" | "following";
}

export default function PostList({ mode = "all" }: PostListProps) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPosts = useCallback(async () => {
    console.log(`Starting to fetch ${mode} posts...`);
    try {
      const posts =
        mode === "following" ? await getFollowingPostApi() : await getPostApi();
      console.log("Received posts:", posts);
      setPosts(posts);
    } catch (err) {
      console.error("Fetch error details:", {
        message: err instanceof Error ? err.message : "Unknown error",
        error: err,
      });
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  }, [mode]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  if (isLoading) {
    return <div className="text-center py-4">Loading posts...</div>;
  }

  if (error) {
    return <div className="text-center text-red-500 py-4">{error}</div>;
  }

  if (posts.length === 0) {
    return <div className="text-center py-4">No posts yet.</div>;
  }

  return (
    <div className="space-y-4">
      {mode === "all" && <CreatePost onPostCreated={() => fetchPosts()} />}
      {posts.map((post) => (
        <Post key={post.id} {...post} onPostUpdate={fetchPosts} />
      ))}
    </div>
  );
}
