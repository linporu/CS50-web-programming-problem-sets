document.addEventListener('DOMContentLoaded', function() {

  // Use buttons to toggle between views
  document.querySelector('#inbox').addEventListener('click', () => loadMailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => loadMailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => loadMailbox('archive'));
  document.querySelector('#compose').addEventListener('click', composeEmail);

  // By default, load the inbox
  loadMailbox('inbox');
});

async function composeEmail() {

  // Show compose view and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#email-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';

  // Clear out composition fields
  document.querySelector('#compose-recipients').value = '';
  document.querySelector('#compose-subject').value = '';
  document.querySelector('#compose-body').value = '';

  // Sent email
  document.querySelector('#compose-form').onsubmit = async function(event){
    event.preventDefault();

    // Check input form
    const recipients = document.querySelector('#compose-recipients').value.trim();
    const subject = document.querySelector('#compose-subject').value.trim();
    const body = document.querySelector('#compose-body').value.trim();

    if (!recipients){
      alert('Recipients field is required.');
      return;
    }
    if (!subject){
      alert('Subject field is required.');
      return;
    }
    if (!body){
      alert('Body field is required.');
      return;
    }

    // POST request
    try {
      await apiRequest(API.EMAILS, {
        method: 'POST',
        body: JSON.stringify({
          recipients: document.querySelector('#compose-recipients').value,
          subject: document.querySelector('#compose-subject').value,
          body: document.querySelector('#compose-body').value
        })
      });
    } catch (error) {
      console.error('Error sending email', error);
      alert(error.message);
    }

    //Load user's sent box
    loadMailbox('sent');
  }
}


async function loadMailbox(mailbox) {
  
  // Show the mailbox and hide other views
  document.querySelector('#emails-view').style.display = 'block';
  document.querySelector('#email-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'none';

  // Show the mailbox name
  document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;

  // Get emails
  try {
    emails = await apiRequest(API.MAILBOX(mailbox));
    renderEmailBox(emails, mailbox);
  } catch (error) {
    console.error('Error getting emails', error);
    alert(error.message);
  }
}


function renderEmailBox(emails, mailbox) {
  // Get container element
  const container = document.querySelector('#emails-view');
  
  // Clear container
  container.innerHTML = '';
  
  // Iterate through emails
  emails.forEach(email => {
    const mailDiv = document.createElement('div');

    mailDiv.classList.add('email-item');
    
    // Change background color to grey after mail is read
    if (!email.read) {
      mailDiv.classList.add('email-unread');
    } else {
      mailDiv.classList.add('email-read');
    }
    
    mailDiv.innerHTML = `
      <div class="email-sender">
        ${email.sender}
      </div>
      <div class="email-subject">
        ${email.subject}
      </div>
      <div class="email-timestamp">
        ${email.timestamp}
      </div>
    `;
    
    mailDiv.addEventListener('click', function() {
      console.log(`Mail #${email.id} has been clicked!`);
      viewEmail(email, mailbox);
    });
    container.append(mailDiv);
  });
}


async function viewEmail(email, mailbox){
  // Show the email and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#email-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';

  // Get and render email
  try {
    await apiRequest(API.EMAIL(email.id));
    renderEmailView(email, mailbox);
  } catch (error) {
    console.error('Error getting email', error);
    alert(error.message);
  }

  // Mark email as read
  try {
    await apiRequest(API.EMAIL(email.id), {
      method: 'PUT',
      body: JSON.stringify({
        read: true
      })
    });
  } catch (error) {
    console.error('Error marking email read', error);
    alert(error.message);
  }
}

function renderEmailView(email, mailbox){
  // Get container element
  const container = document.querySelector('#email-view');
  
  // Clear container
  container.innerHTML = '';
  
  // Create email view element
  const emailView = document.createElement('div');
  emailView.classList.add('email-view');

  emailView.innerHTML = `
    <div class="email-sender">
      <strong>From:</strong> ${email.sender}
    </div>
    <div class="email-recipients">
      <strong>To:</strong> ${email.recipients}
    </div>
    <div class="email-subject">
      <strong>Subject:</strong> ${email.subject}
    </div>
    <div class="email-timestamp">
      <strong>Timestamp:</strong> ${email.timestamp}
    </div>
    <div class="email-body"> 
      ${email.body}
    </div>
  `;

  container.append(emailView);

  // Archive and unarchive
  // Only show archive button if the user is not the sender (not in sent mailbox)
  if (mailbox !== 'sent') {
    //Create archive button
    const archiveButton = document.createElement('button');
    archiveButton.classList.add('archive-button');
    archiveButton.textContent = email.archived ? 'Unarchive' : 'Archive';
    container.append(archiveButton);

    // Click button to archive email
    archiveButton.addEventListener('click', () => toggleArchive(email));
  }

  // Reply button
  //Create reply button
  const replyButton = document.createElement('button');
  replyButton.classList.add('reply-button');
  replyButton.textContent = 'Reply';
  container.append(replyButton);

  // Click reply button to reply email
  replyButton.addEventListener('click', () => reply(email));
}

async function toggleArchive(email) {
  try {
    await apiRequest(API.EMAIL(email.id), {
      method: 'PUT',
      body: JSON.stringify({
        archived: !email.archived  // Toggle the archived status
      })
    });
    // TODO: put this after reply(email) in reply button
    loadMailbox('inbox');
  } catch (error) {
    console.error('Error getting email', error);
    alert(error.message);
  }
}


function reply(email){
  composeEmail();

  // Prefill the composition form
  document.querySelector('#compose-recipients').value = `${email.sender}`;
  document.querySelector('#compose-subject').value = 
    email.subject.startsWith('Re:') ? email.subject : `Re: ${email.subject}`;
  document.querySelector('#compose-body').value = `
    On ${email.timestamp} ${email.sender} wrote: 
    ${email.body}
  `;
}


// Define API endpoints
const API = {
  EMAILS: '/emails',
  EMAIL: (id) => `/emails/${id}`,
  MAILBOX: (mailbox) => `/emails/${mailbox}`,
}


async function apiRequest(url, options = {}) {
  // 1. Set default options
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',  // Set data format to JSON
    },
    credentials: 'same-origin',  // Set cookie handling method
  };

  try {
    // 2. Send request and wait for response
    const response = await fetch(url, { 
      ...defaultOptions,  // Spread default options
      ...options         // Spread user provided options (will override defaults)
    });
    
    // 3. Check HTTP status
    if (!response.ok) {
      // If status code is not 2xx, throw error
      throw new Error(`HTTP error! status: ${response.status}`);
    }

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
    throw error;  // Re-throw error up the chain
  }
}