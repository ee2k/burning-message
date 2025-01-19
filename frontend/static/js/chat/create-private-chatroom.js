import { initSvgIcons } from '../global.js';
import { $ } from '../utils/dom.js';
import { loadComponent } from '../utils/components.js';

document.addEventListener('DOMContentLoaded', async () => {
    // Load header component
    await loadComponent('headerComponent', '/components/header');
    
    // Initialize global features
    initSvgIcons();

    // Setup custom ID section
    const customIDBtn = $('#customIDBtn');
    const idInputContainer = $('#idInputContainer');
    const customID = $('#customID');
    const idCounter = $('#idCounter');

    customIDBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const isHidden = !idInputContainer.classList.contains('show');
        
        // Toggle button state
        customIDBtn.classList.toggle('active');
        
        // Show container before animation
        if (isHidden) {
            idInputContainer.style.display = 'block';
            setTimeout(() => {
                idInputContainer.classList.add('show');
            }, 10);
        } else {
            idInputContainer.classList.remove('show');
            setTimeout(() => {
                idInputContainer.style.display = 'none';
                customID.value = ''; // Clear the textarea when folded
                idCounter.textContent = 70; // Reset character counter
            }, 300);
        }
    });

    // Setup custom token section
    const customTokenBtn = $('#customTokenBtn');
    const tokenInputContainer = $('#tokenInputContainer');
    const customToken = $('#customToken');
    const tokenHint = $('#tokenHint');
    const tokenCounter = $('#tokenCounter');
    const hintCounter = $('#hintCounter');

    customTokenBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const isHidden = !tokenInputContainer.classList.contains('show');
        
        // Toggle button state
        customTokenBtn.classList.toggle('active');
        
        // Show container before animation
        if (isHidden) {
            tokenInputContainer.style.display = 'block';
            setTimeout(() => {
                tokenInputContainer.classList.add('show');
            }, 10);
        } else {
            tokenInputContainer.classList.remove('show');
            setTimeout(() => {
                tokenInputContainer.style.display = 'none';
                customToken.value = ''; // Clear the textarea when folded
                tokenCounter.textContent = 70; // Reset character counter
                tokenHint.value = ''; // Clear token hint
                hintCounter.textContent = 70; // Reset hint counter
            }, 300);
        }
    });

    // Setup character counters
    function setupCounter(textarea, counter, maxLength) {
        counter.textContent = maxLength;
        textarea.addEventListener('input', () => {
            const remaining = maxLength - textarea.value.length;
            counter.textContent = remaining;
        });
    }

    setupCounter(customID, idCounter, 70);
    setupCounter(customToken, tokenCounter, 70);
    setupCounter(tokenHint, hintCounter, 70);

    // Modify the existing room creation handler
    document.getElementById('createBtn').addEventListener('click', async () => {
        const customRoomId = customID.value.trim();
        const token = customToken.value.trim();
        const hint = tokenHint.value.trim();

        // Check if the user has chosen to use custom chatroom ID or token
        const isCustomIDActive = customIDBtn.classList.contains('active');
        const isCustomTokenActive = customTokenBtn.classList.contains('active');

        // Validation checks only if the corresponding toggle is active
        if (isCustomIDActive && !customRoomId) {
            alert('Please enter at least 1 char for Custom Chatroom ID.');
            return;
        }

        if (isCustomTokenActive && !token) {
            alert('Please enter at least 1 char for Access Token.');
            return;
        }

        try {
            const response = await fetch('/api/chat/private_room/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    room_id: customRoomId || undefined,
                    room_token: token || undefined,
                    room_token_hint: hint || undefined
                })
            });

            if (!response.ok) throw new Error('Failed to create room');

            const data = await response.json();
            window.location.href = `/private-chatroom-created`;
        } catch (error) {
            console.error('Error creating room:', error);
            alert('Failed to create room. Please try again.');
        }
    });
});