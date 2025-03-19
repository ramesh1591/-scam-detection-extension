chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "check_scam") {
      console.log("Received URL:", request.url);

      // Validate the URL
      if (!request.url || !request.url.startsWith("http")) {
          sendResponse({ error: "Invalid URL format." });
          return;
      }

      // Send the URL to the Flask API for scam detection
      fetch("http://127.0.0.1:5000/api/detect", {
          method: "POST",
          headers: {
              "Content-Type": "application/json",
          },
          body: JSON.stringify({ url: request.url }),
      })
          .then((response) => {
              if (!response.ok) {
                  throw new Error("Failed to connect to the server.");
              }
              return response.json();
          })
          .then((data) => {
              console.log("Detection Result:", data);
              sendResponse(data); // Send the API response back to the sender
          })
          .catch((error) => {
              console.error("Error:", error.message);
              sendResponse({ error: "Error contacting scam detection service." });
          });

      // Return true to indicate sendResponse will be called asynchronously
      return true;
  }
});
