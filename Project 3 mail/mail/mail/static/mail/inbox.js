// Define API endpoints for backend communication
const API = {
  EMAILS: '/emails',                           // Endpoint for sending new emails
  EMAIL: (id) => `/emails/${id}`,             // Endpoint for getting/modifying specific emails
  MAILBOX: (mailbox) => `/emails/${mailbox}`,  // Endpoint for getting specific mailbox (inbox/sent etc)
}

// Wrapper function for all API requests
async function apiRequest(url, options = {}) {
  // 1. Set default options
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',  // Set data format to JSON
    },
    credentials: 'same-origin',  // Set to use same-origin cookies
  };

  try {
    // 2. Send request and await response
    const response = await fetch(url, { 
      ...defaultOptions,  // Spread default options
      ...options         // Spread user options (will override defaults)
    });
    
    // 3. Check HTTP status
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // If status code is 204 (No Content), return null directly
    if (response.status === 204) {
      return null;
    }

    // 4. Parse JSON response
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
    // 5. Error handling
    console.error('API Request failed:', error);
    alert(error.message);
    throw error;  // Rethrow error
  }
}

// Main App component
function App() {
  // Use React.useState to manage state
  const [currentMailbox, setCurrentMailbox] = React.useState('inbox');  // Currently selected mailbox
  const [emails, setEmails] = React.useState([]);                       // List of emails in mailbox
  const [selectedEmail, setSelectedEmail] = React.useState(null);       // Currently selected email
  const [view, setView] = React.useState('list');                      // Current view ('list', 'compose', 'email')
  const [replyData, setReplyData] = React.useState(null);              // Default data when replying to email

  // Handle mailbox switching
  const handleMailboxClick = async (mailbox) => {
    if (mailbox === 'compose') {
      setView('compose');  // If clicking compose, switch to compose view
    } else {
      try {
        // Get all emails for the mailbox
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

  // Handle email click
  const handleEmailClick = async (email) => {
    try {
      // Get full email content
      const fullEmail = await apiRequest(API.EMAIL(email.id));
      setSelectedEmail(fullEmail);
      setView('email');

      // Mark email as read
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

  // Handle email sent completion
  const handleEmailSent = () => {
    handleMailboxClick('sent');  // Switch to sent box after sending
  };

  // Handle logout
  const handleLogout = () => {
    window.location.href = '/logout';  // Assuming Django logout URL is /logout
  };

  // Use useEffect to load inbox on first render
  React.useEffect(() => {
    handleMailboxClick('inbox');
  }, []);

  // Render UI
  return (
    <div>
      {/* Sidebar containing mailbox buttons */}
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
        <button 
          className="btn btn-sm btn-outline-danger" 
          onClick={handleLogout}
        >
          Logout
        </button>
      </div>
      
      {/* Display different components based on current view */}
      {/* Compose email view */}
      {view === 'compose' && (
        <ComposeEmail 
          onEmailSent={handleEmailSent}
          initialData={replyData}
        />
      )}
      
      {/* Mailbox view */}
      {view === 'list' && (
        <div id="emails-view">
          <h3>{currentMailbox.charAt(0).toUpperCase() + currentMailbox.slice(1)}</h3>
          <EmailList emails={emails} onEmailClick={handleEmailClick} />
        </div>
      )}
      
      {/* Email detail view */}
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

// Compose email component
function ComposeEmail({ onEmailSent, initialData }) {
  // Manage form state
  const [recipients, setRecipients] = React.useState(initialData && initialData.recipients ? initialData.recipients : '');
  const [subject, setSubject] = React.useState(initialData && initialData.subject ? initialData.subject : '');
  const [body, setBody] = React.useState(initialData && initialData.body ? initialData.body : '');

  // Handle form submission
  const handleSubmit = async (event) => {
    event.preventDefault();

    // Form validation
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
      // Send email
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

  // Render compose email form
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

// Email list component
function EmailList({ emails, onEmailClick }) {
  return (
    <div>
      {/* Iterate and render each email */}
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

// Email detail view component
function EmailView({ email, mailbox, onBack, setView, setReplyData, onArchive }) {
  // Handle archive/unarchive
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

  // Handle reply to email
  const handleReply = () => {
    // Set default values for reply email
    const replySubject = email.subject.startsWith('Re: ') 
      ? email.subject 
      : `Re: ${email.subject}`;
      
    const replyBody = `
On ${email.timestamp} ${email.sender} wrote:
${email.body}
    `;

    // Update ComposeEmail state
    setView('compose');
    setReplyData({
      recipients: email.sender,
      subject: replySubject,
      body: replyBody
    });
  };

  // Render email details
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

// Render App component to DOM
ReactDOM.render(<App />, document.getElementById('app'));
