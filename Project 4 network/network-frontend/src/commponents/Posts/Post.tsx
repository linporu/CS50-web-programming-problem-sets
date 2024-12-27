interface PostProps {
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
}

export default function Post({
  content,
  created_by,
  created_at,
  updated_at,
  likes_count,
  comments_count,
}: PostProps) {
  //   function handleEdit() {}
  //   function handleLike() {}
  //   function handleComment() {}

  return (
    <div className="rounded-lg border border-gray-200 p-4 shadow-sm">
      {/* Post Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {/* 可以之後加入用戶頭像 */}
          <span className="font-medium">{created_by}</span>
          <span className="text-sm text-gray-500">
            {updated_at ? updated_at : created_at}
          </span>
        </div>
        {/* 之後可以加入 More 選單 (編輯、刪除等功能) */}
      </div>

      {/* Post Content */}
      <p className="mb-4">{content}</p>

      {/* Post Footer */}
      <div className="flex items-center gap-4 text-sm text-gray-600">
        <button className="flex items-center gap-1 hover:text-blue-500">
          <span>Like</span>
          <span>{likes_count}</span>
        </button>

        <button className="flex items-center gap-1 hover:text-blue-500">
          <span>Comment</span>
          <span>{comments_count}</span>
        </button>
      </div>
    </div>
  );
}
