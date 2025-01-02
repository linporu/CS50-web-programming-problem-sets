import PostList from "../components/Posts/PostList";

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold mb-6">All Posts</h2>
      <PostList mode="all" />
    </div>
  );
}
