# How to Export Facebook Cookies

To use The Facebook Eye with a logged-in session, you need to export your Facebook cookies from your browser after logging in manually. This allows the tool to make requests as if it were you.

**Recommended Method: Using a Browser Extension**

The easiest way to export cookies is by using a browser extension designed for this purpose. Here are a few popular options:

*   **Get cookies.txt** (Chrome, Firefox): Exports cookies in the Netscape standard `cookies.txt` format. You might need to convert this to JSON.
*   **EditThisCookie** (Chrome, Opera): Allows you to view, edit, and export cookies in JSON format. This is often the most straightforward for this tool.
*   **Cookie-Editor** (Chrome, Firefox, Edge, Opera): Another popular extension that can export cookies in JSON format.

**Steps using an extension like EditThisCookie or Cookie-Editor:**

1.  Install the extension in your Chrome or Firefox browser.
2.  Log in to your Facebook account as you normally would.
3.  Click on the extension's icon in your browser toolbar while you are on a Facebook page.
4.  Look for an "Export" or "Export All" button. Choose JSON format if available.
5.  Save the exported cookies as a file named `cookies.json` in the root directory of The Facebook Eye project.

**Example JSON Structure for `cookies.json`:**

The file should be an array of cookie objects. Here's a simplified example of what one cookie object might look like:

```json
[
  {
    "name": "c_user",
    "value": "YOUR_FACEBOOK_USER_ID",
    "domain": ".facebook.com",
    "path": "/",
    "expires": 17xxxxxxxxx, // Timestamp
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  },
  {
    "name": "xs",
    "value": "YOUR_XS_COOKIE_VALUE",
    "domain": ".facebook.com",
    "path": "/",
    "expires": 17xxxxxxxxx, // Timestamp
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  }
  // ... other cookies
]
```

**Important Security Notes:**

*   **Your cookies are sensitive data.** They grant access to your Facebook account. Do not share your `cookies.json` file with anyone.
*   Keep the `cookies.json` file in a secure location and ensure it's included in your `.gitignore` if you're using a private repository (though it's already in the project's default `.gitignore`).
*   Cookies expire. You may need to re-export your cookies periodically.

**Manual Method (Using Browser Developer Tools - More Technical):**

1.  Log in to Facebook.
2.  Open your browser's developer tools (usually by pressing F12).
3.  Go to the "Application" (Chrome) or "Storage" (Firefox) tab.
4.  Find "Cookies" in the left-hand panel and select `https://www.facebook.com`.
5.  You will see a list of cookies. You'll need to manually copy the `name`, `value`, `domain`, `path`, `expires` (you might need to convert the date/time to a timestamp), `httpOnly`, `secure`, and `sameSite` properties for essential cookies (like `c_user`, `xs`, etc.) and construct the JSON array as shown above. This method is more error-prone.

Using an extension is highly recommended for ease and accuracy.
