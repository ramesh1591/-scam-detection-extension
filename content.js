// Listen for messages from the background script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "extract_content") {
        // Extract visible text content from the current webpage
        const pageContent = document.body.innerText || "";
        sendResponse({ content: pageContent.slice(0, 10000) }); // Limit to 10,000 characters for performance
    }
});

// Function to highlight scam-related content on the webpage
function highlightScamContent(selector, isScam) {
    const elements = document.querySelectorAll(selector);
    elements.forEach((element) => {
        element.style.border = isScam ? "2px solid red" : "2px solid green";
        element.style.backgroundColor = isScam ? "#ffcccc" : "#ccffcc";
    });
}

// Example usage of content manipulation (optional for advanced features)
// Inject custom elements or visual indicators based on detection
function injectIndicator(isScam) {
    const indicator = document.createElement("div");
    indicator.style.position = "fixed";
    indicator.style.bottom = "10px";
    indicator.style.right = "10px";
    indicator.style.padding = "10px";
    indicator.style.borderRadius = "5px";
    indicator.style.color = "white";
    indicator.style.backgroundColor = isScam ? "red" : "green";
    indicator.style.zIndex = 10000;
    indicator.textContent = isScam ? "Warning: Scam Detected!" : "This page seems legitimate.";
    document.body.appendChild(indicator);

    setTimeout(() => indicator.remove(), 5000); // Remove after 5 seconds
}

// Export content.js functions (optional for modularization)
export { highlightScamContent, injectIndicator };
