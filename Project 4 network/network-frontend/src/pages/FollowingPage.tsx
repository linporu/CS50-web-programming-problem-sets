import PostList from "../components/Posts/PostList";

export default function FollowingPage() {

  return (
    <div className="container mx-auto px-4">
      <h1 className="text-2xl font-bold mb-4">Following Posts</h1>
      <PostList
        mode="following"
      />
    </div>
  );
}
