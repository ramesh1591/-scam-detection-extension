document.addEventListener("DOMContentLoaded", function () {
    let detectBtn = document.getElementById("detectBtn");
    let resultDiv = document.getElementById("result");
    let scamAlert = document.getElementById("scamAlert"); // Sound Alert

    detectBtn.addEventListener("click", function () {
        detectBtn.disabled = true; // Disable button to prevent multiple clicks
        detectBtn.textContent = "Checking...";
        resultDiv.style.display = "none"; // Hide result box until API responds

        // Get the current active tab
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            let currentUrl = tabs[0].url;
            let apiUrl = "http://localhost:5000/api/detect";  // Update if API is hosted remotely

            // Send the URL to the Flask API
            fetch(apiUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json; charset=UTF-8" },  // 🔹 Force UTF-8 encoding
                body: JSON.stringify({ url: currentUrl })
            })
            .then(response => response.json())
            .then(data => {
                resultDiv.style.display = "block"; // Show result box

                if (data.result === "Scam") {
                    resultDiv.textContent = "🚨 Scam Detected!\n" + data.message;
                    resultDiv.classList.add("error"); // Apply red background
                    resultDiv.classList.remove("success");
                    scamAlert.play(); // 🔊 Play sound alert for scam sites
                } else {
                    resultDiv.textContent = "✅ Legitimate Site\n" + data.message;
                    resultDiv.classList.add("success"); // Apply green background
                    resultDiv.classList.remove("error");
                }
            })
            .catch(error => {
                resultDiv.style.display = "block";
                resultDiv.textContent = "❌ Error: Could not connect to API.";
                resultDiv.classList.add("error");
                console.error("API Error:", error);
            })
            .finally(() => {
                detectBtn.disabled = false; // Re-enable button after API response
                detectBtn.textContent = "Check Current Page";
            });
        });
    });
});
