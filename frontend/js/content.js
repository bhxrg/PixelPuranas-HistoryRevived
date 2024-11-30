document.getElementById('generateContentBtn').addEventListener('click', async function () {
    const prompt = document.getElementById('promptInput').value.trim();

    if (prompt === '') {
        alert('Please enter a prompt.');
        return;
    }

    // Show loading state
    document.getElementById('contentSection').style.display = 'block';
    document.getElementById('generatedContent').innerHTML = '<p>Loading content...</p>';

    try {
        // Send prompt to backend
        const response = await fetch('http://127.0.0.1:5000/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt: prompt }),
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        // Display generated text
        const generatedContent = `
            <h3>Generated Text:</h3>
            <p>${data.text || 'No text generated.'}</p>
            <h3>Generated Images:</h3>
        `;
        document.getElementById('generatedContent').innerHTML = generatedContent;
        if (data.images && data.images.length > 0) {
            const imageContainer = document.createElement('div');
            data.images.forEach((img, index) => {
                const imageElement = document.createElement('img');
                imageElement.src = `data:image/png;base64,${img}`;
                imageElement.alt = `Generated Image ${index + 1}`;
                imageElement.className = 'img-fluid mb-3';
                imageContainer.appendChild(imageElement);
            });
            document.getElementById('generatedContent').appendChild(imageContainer);
        } else {
            document.getElementById('generatedContent').innerHTML += '<p>No images generated.</p>';
        }
        
        // Add PDF download
        if (data.pdf) {
            const pdfDownloadLink = `<a href="data:application/pdf;base64,${data.pdf}" download="Generated_Content.pdf" class="btn btn-primary mt-3">Download PDF</a>`;
            document.getElementById('generatedContent').innerHTML += pdfDownloadLink;
        }

        // Add video preview and download
        if (data.video) {
            const videoHTML = `
                <h3>Generated Video:</h3>
                <video controls width="100%">
                    <source src="data:video/mp4;base64,${data.video}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <a href="data:video/mp4;base64,${data.video}" download="Generated_Video.mp4" class="btn btn-primary mt-3">Download Video</a>
            `;
            document.getElementById('generatedContent').innerHTML += videoHTML;
        }

        // Fetch recommendations
        const recommendations = ['Freedom Struggle', 'Mughal Empire', 'Indus Valley Civilization']; // Replace with dynamic recommendations if backend provides them
        const recommendationList = document.getElementById('recommendationList');
        recommendationList.innerHTML = '';
        recommendations.forEach(topic => {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item';
            listItem.textContent = topic;
            recommendationList.appendChild(listItem);
        });

        document.getElementById('recommendationSection').style.display = 'block';

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('generatedContent').innerHTML = `<p class="text-danger">Failed to generate content. Please try again later.</p>`;
    }
});

document.getElementById('askChatBotBtn').addEventListener('click', async function () {
    const question = document.getElementById('chatInput').value.trim();

    if (question === '') {
        alert('Please ask a question.');
        return;
    }

    // Show loading state for chatbot
    const chatResponseElement = document.getElementById('chatResponse');
    chatResponseElement.innerText = 'Thinking...';

    try {
        // Send question to backend chatbot endpoint
        const response = await fetch('http://127.0.0.1:5000/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question }),
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        // Display chatbot response
        chatResponseElement.innerText = data.response || 'No response from chatbot.';
    } catch (error) {
        console.error('Error:', error);
        chatResponseElement.innerText = 'Failed to get a response. Please try again later.';
    }
});
