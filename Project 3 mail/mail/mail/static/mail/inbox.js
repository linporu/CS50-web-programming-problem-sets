// 定義 API 端點，用於與後端溝通
const API = {
  EMAILS: '/emails',                           // 用於發送新郵件的端點
  EMAIL: (id) => `/emails/${id}`,             // 用於獲取/修改特定郵件的端點
  MAILBOX: (mailbox) => `/emails/${mailbox}`,  // 用於獲取特定信箱(收件匣/寄件匣等)的端點
}

// 封裝所有 API 請求的通用函數
async function apiRequest(url, options = {}) {
  // 1. 設定預設選項
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',  // 設定資料格式為 JSON
    },
    credentials: 'same-origin',  // 設定使用同源 cookie
  };

  try {
    // 2. 發送請求並等待回應
    const response = await fetch(url, { 
      ...defaultOptions,  // 展開預設選項
      ...options         // 展開使用者提供的選項(會覆蓋預設值)
    });
    
    // 3. 檢查 HTTP 狀態
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // 如果狀態碼是 204 (No Content)，直接返回 null
    if (response.status === 204) {
      return null;
    }

    // 4. 解析 JSON 回應
    try {
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      return data;
    } catch (jsonError) {
      throw new Error('Invalid response format from server');
    }
  } catch (error) {
    // 5. 錯誤處理
    console.error('API Request failed:', error);
    alert(error.message);
    throw error;  // 將錯誤往上拋出
  }
}

// 主要的 App 組件
function App() {
  // 使用 React.useState 管理狀態
  const [currentMailbox, setCurrentMailbox] = React.useState('inbox');  // 當前選擇的信箱
  const [emails, setEmails] = React.useState([]);                       // 信箱中的郵件列表
  const [selectedEmail, setSelectedEmail] = React.useState(null);       // 當前選中的郵件
  const [view, setView] = React.useState('list');                      // 當前視圖('list', 'compose', 'email')
  const [replyData, setReplyData] = React.useState(null);              // 回覆郵件時的預設資料

  // 處理信箱切換的函數
  const handleMailboxClick = async (mailbox) => {
    if (mailbox === 'compose') {
      setView('compose');  // 如果點擊撰寫郵件，切換到撰寫視圖
    } else {
      try {
        // 獲取該信箱的所有郵件
        const emails = await apiRequest(API.MAILBOX(mailbox));
        setEmails(emails);
        setCurrentMailbox(mailbox);
        setSelectedEmail(null);
        setView('list');
      } catch (error) {
        console.error('Error getting emails', error);
      }
    }
  };

  // 處理點擊郵件的函數
  const handleEmailClick = async (email) => {
    try {
      // 獲取完整的郵件內容
      const fullEmail = await apiRequest(API.EMAIL(email.id));
      setSelectedEmail(fullEmail);
      setView('email');

      // 將郵件標記為已讀
      await apiRequest(API.EMAIL(email.id), {
        method: 'PUT',
        body: JSON.stringify({
          read: true
        })
      });
    } catch (error) {
      console.error('Error viewing email', error);
    }
  };

  // 處理郵件發送完成的函數
  const handleEmailSent = () => {
    handleMailboxClick('sent');  // 發送完成後切換到寄件匣
  };

  // 新增處理登出的函數
  const handleLogout = () => {
    window.location.href = '/logout';  // 假設 Django 的登出 URL 是 /logout
  };

  // 使用 useEffect 在組件首次渲染時載入收件匣
  React.useEffect(() => {
    handleMailboxClick('inbox');
  }, []);

  // 渲染 UI
  return (
    <div>
      {/* 側邊欄，包含各種信箱按鈕 */}
      <div className="sidebar">
        <button 
          className="btn btn-sm btn-outline-primary" 
          onClick={() => handleMailboxClick('inbox')}
        >
          Inbox
        </button>
        <button 
          className="btn btn-sm btn-outline-primary" 
          onClick={() => handleMailboxClick('compose')}
        >
          Compose
        </button>
        <button 
          className="btn btn-sm btn-outline-primary" 
          onClick={() => handleMailboxClick('sent')}
        >
          Sent
        </button>
        <button 
          className="btn btn-sm btn-outline-primary" 
          onClick={() => handleMailboxClick('archive')}
        >
          Archived
        </button>
        {/* 新增登出按鈕 */}
        <button 
          className="btn btn-sm btn-outline-danger" 
          onClick={handleLogout}
        >
          Logout
        </button>
      </div>
      
      {/* 根據當前視圖顯示不同的組件 */}
      {/* 撰寫郵件視圖 */}
      {view === 'compose' && (
        <ComposeEmail 
          onEmailSent={handleEmailSent}
          initialData={replyData}
        />
      )}
      
      {/* 信箱視圖 */}
      {view === 'list' && (
        <div id="emails-view">
          <h3>{currentMailbox.charAt(0).toUpperCase() + currentMailbox.slice(1)}</h3>
          <EmailList emails={emails} onEmailClick={handleEmailClick} />
        </div>
      )}
      
      {/* 郵件詳情視圖 */}
      {view === 'email' && selectedEmail && (
        <EmailView 
          email={selectedEmail} 
          mailbox={currentMailbox}
          onBack={() => setView('list')}
          setView={setView}
          setReplyData={setReplyData}
          onArchive={() => handleMailboxClick('inbox')}
        />
      )}
    </div>
  );
}

// 撰寫郵件組件
function ComposeEmail({ onEmailSent, initialData }) {
  // 管理表單狀態
  const [recipients, setRecipients] = React.useState(initialData && initialData.recipients ? initialData.recipients : '');
  const [subject, setSubject] = React.useState(initialData && initialData.subject ? initialData.subject : '');
  const [body, setBody] = React.useState(initialData && initialData.body ? initialData.body : '');

  // 處理表單提交
  const handleSubmit = async (event) => {
    event.preventDefault();

    // 表單驗證
    if (!recipients.trim()) {
      alert('Recipients field is required.');
      return;
    }
    if (!subject.trim()) {
      alert('Subject field is required.');
      return;
    }
    if (!body.trim()) {
      alert('Body field is required.');
      return;
    }

    try {
      // 發送郵件
      await apiRequest(API.EMAILS, {
        method: 'POST',
        body: JSON.stringify({
          recipients: recipients,
          subject: subject,
          body: body
        })
      });
      onEmailSent();
    } catch (error) {
      console.error('Error sending email', error);
      alert(error.message);
    }
  };

  // 渲染撰寫郵件表單
  return (
    <div id="compose-view">
      <h3>New Email</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <input 
            type="text" 
            className="form-control" 
            placeholder="Recipients" 
            value={recipients}
            onChange={(e) => setRecipients(e.target.value)}
          />
        </div>
        <div className="form-group">
          <input 
            type="text" 
            className="form-control" 
            placeholder="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
          />
        </div>
        <div className="form-group">
          <textarea 
            className="form-control" 
            placeholder="Body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
        </div>
        <button type="submit" className="btn btn-primary">Send</button>
      </form>
    </div>
  );
}

// 郵件列表組件
function EmailList({ emails, onEmailClick }) {
  return (
    <div>
      {/* 遍歷並渲染每封郵件 */}
      {emails.map(email => (
        <div 
          key={email.id} 
          className={`email-item ${email.read ? 'email-read' : 'email-unread'}`}
          onClick={() => onEmailClick(email)}
        >
          <div className="email-sender">{email.sender}</div>
          <div className="email-subject">{email.subject}</div>
          <div className="email-timestamp">{email.timestamp}</div>
        </div>
      ))}
    </div>
  );
}

// 郵件詳情視圖組件
function EmailView({ email, mailbox, onBack, setView, setReplyData, onArchive }) {
  // 處理封存/取消封存
  const handleArchive = async () => {
    try {
      await apiRequest(API.EMAIL(email.id), {
        method: 'PUT',
        body: JSON.stringify({
          archived: !email.archived
        })
      });
      onBack();
      onArchive();
    } catch (error) {
      console.error('Error archiving email', error);
    }
  };

  // 處理回覆郵件
  const handleReply = () => {
    // 設定回覆郵件的預設值
    const replySubject = email.subject.startsWith('Re: ') 
      ? email.subject 
      : `Re: ${email.subject}`;
      
    const replyBody = `
On ${email.timestamp} ${email.sender} wrote:
${email.body}
    `;

    // 更新 ComposeEmail 的狀態
    setView('compose');
    setReplyData({
      recipients: email.sender,
      subject: replySubject,
      body: replyBody
    });
  };

  // 渲染郵件詳情
  return (
    <div className="email-view">
      <div className="email-sender">
        <strong>From:</strong> {email.sender}
      </div>
      <div className="email-recipients">
        <strong>To:</strong> {email.recipients.join(', ')}
      </div>
      <div className="email-subject">
        <strong>Subject:</strong> {email.subject}
      </div>
      <div className="email-timestamp">
        <strong>Timestamp:</strong> {email.timestamp}
      </div>
      <div className="email-body">
        {email.body}
      </div>
      <button onClick={onBack}>Back</button>
      {mailbox !== 'sent' && (
        <button onClick={handleArchive}>
          {email.archived ? 'Unarchive' : 'Archive'}
        </button>
      )}
      <button onClick={handleReply}>Reply</button>
    </div>
  );
}

// 將 App 組件渲染到 DOM
ReactDOM.render(<App />, document.getElementById('app'));
