import { useEffect, useState, useCallback } from "react";
import Post from "./Post";
import {
  getFollowingPostApi,
  getAllPostsApi,
} from "../../services/postService";
import { getUserPostsApi } from "../../services/userService";
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
  is_liked: boolean;
  comments: {
    id: number;
    content: string;
    created_by: string;
    created_at: string;
    is_deleted: boolean;
  }[];
};

interface PostListProps {
  mode?: "all" | "following" | "user";
  username?: string;
}

export default function PostList({ mode = "all", username }: PostListProps) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPosts = useCallback(async () => {
    console.log(`Starting to fetch ${mode} posts...`);
    try {
      let posts;
      if (mode === "following") {
        posts = await getFollowingPostApi();
      } else if (mode === "user") {
        if (!username) {
          throw new Error("Username is required for user mode");
        }
        posts = await getUserPostsApi(username);
      } else {
        posts = await getAllPostsApi();
      }
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
  }, [mode, username]);

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
        <Post
          key={post.id}
          {...post}
          is_liked={post.is_liked || false}
          onPostUpdate={fetchPosts}
        />
      ))}
    </div>
  );
}
