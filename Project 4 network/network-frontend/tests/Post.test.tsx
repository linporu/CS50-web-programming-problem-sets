import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Post from "../src/components/Posts/Post";

describe("Post Component", () => {
  const mockPostProps = {
    id: 1,
    content: "Test post content",
    created_by: "testuser",
    created_at: "2024-03-20T10:00:00Z",
    updated_at: "",
    is_deleted: false,
    likes_count: 5,
    comments_count: 3,
    comments: [
      {
        id: 1,
        content: "Test comment",
        created_by: "commenter",
        created_at: "2024-03-20T10:01:00Z",
        is_deleted: false,
      },
    ],
  };

  // 測試基本渲染
  it("renders post content correctly", () => {
    render(<Post {...mockPostProps} />);

    expect(screen.getByText("Test post content")).toBeDefined();
    expect(screen.getByText("testuser")).toBeDefined();
  });

  // 測試時間顯示邏輯
  it("shows created_at when updated_at is empty", () => {
    render(<Post {...mockPostProps} />);
    expect(screen.getByText("2024-03-20T10:00:00Z")).toBeDefined();
  });

  it("shows updated_at when available", () => {
    const updatedProps = {
      ...mockPostProps,
      updated_at: "2024-03-20T11:00:00Z",
    };
    render(<Post {...updatedProps} />);
    expect(screen.getByText("2024-03-20T11:00:00Z")).toBeDefined();
  });

  // 測試互動計數器
  it("displays correct likes count", () => {
    render(<Post {...mockPostProps} />);
    const likeButton = screen.getByText("Like");
    expect(likeButton.nextElementSibling).toHaveTextContent("5");
  });

  it("displays correct comments count", () => {
    render(<Post {...mockPostProps} />);
    const commentButton = screen.getByText("Comment");
    expect(commentButton.nextElementSibling).toHaveTextContent("3");
  });

  // 測試按鈕互動
  it("like button is clickable", async () => {
    const user = userEvent.setup();
    render(<Post {...mockPostProps} />);

    const likeButton = screen.getByText("Like")
      .parentElement as HTMLButtonElement;
    expect(likeButton).toBeEnabled();
    await user.click(likeButton);
  });

  it("comment button is clickable", async () => {
    const user = userEvent.setup();
    render(<Post {...mockPostProps} />);

    const commentButton = screen.getByText("Comment")
      .parentElement as HTMLButtonElement;
    expect(commentButton).toBeEnabled();
    await user.click(commentButton);
  });
});
