// Complete Notes Fix Script
// This script fixes all issues with the Study Notes functionality

document.addEventListener('DOMContentLoaded', function() {
    console.log('Complete Notes Fix: Initializing...');
    
    // Wait for other scripts to load
    setTimeout(function() {
        // Ensure global variables are available
        if (typeof window.currentlyEditingNoteId === 'undefined') {
            window.currentlyEditingNoteId = null;
        }
        
        // Initialize notes storage
        let notesStorage = JSON.parse(localStorage.getItem('pythonStudyNotes') || '[]');
        
        // Helper function to get topic text from value
        function getTopicText(topicValue) {
            const topicOptions = {
                'python-basics': 'Python Basics',
                'data-types': 'Data Types',
                'functions': 'Functions',
                'oop': 'Object-Oriented Programming',
                'libraries': 'Python Libraries',
                'control-flow': 'Control Flow',
                'data-structures': 'Data Structures',
                'algorithms': 'Algorithms'
            };
            return topicOptions[topicValue] || 'Uncategorized';
        }
        
        // Function to save notes to localStorage
        function saveNotesToStorage() {
            localStorage.setItem('pythonStudyNotes', JSON.stringify(notesStorage));
            console.log('Notes saved to localStorage:', notesStorage.length, 'notes');
        }
        
        // Function to update notes count display
        function updateNotesCount() {
            const totalNotes = document.querySelectorAll('.note-item').length;
            const notesCountElement = document.getElementById('notes-count');
            if (notesCountElement) {
                notesCountElement.textContent = `${totalNotes} notes`;
            }
            console.log('Updated notes count:', totalNotes);
        }
        
        // Function to reset note highlights
        function resetNoteHighlights() {
            const allNotes = document.querySelectorAll('.note-item');
            allNotes.forEach(note => {
                note.style.border = '1px solid #e9ecef';
                note.style.backgroundColor = '';
            });
        }
        
        // Function to reset edit mode
        function resetEditMode() {
            window.currentlyEditingNoteId = null;
            const saveBtn = document.getElementById('save-note-btn');
            const notesArea = document.getElementById('notes-area');
            const topicSelector = document.getElementById('note-topic-selector');
            const cancelBtn = document.getElementById('cancel-edit-btn');
            
            if (saveBtn) saveBtn.textContent = 'Save';
            if (notesArea) notesArea.value = '';
            if (topicSelector) topicSelector.value = '';
            if (cancelBtn) cancelBtn.style.display = 'none';
            
            resetNoteHighlights();
            console.log('Edit mode reset');
        }
        
        // Function to show notification
        function showNotification(message) {
            if (typeof window.showNotification === 'function') {
                window.showNotification(message);
            } else {
                console.log('Notification:', message);
                // Simple fallback notification
                const notification = document.getElementById('notification');
                const notificationText = document.getElementById('notification-text');
                if (notification && notificationText) {
                    notificationText.textContent = message;
                    notification.classList.add('show');
                    setTimeout(() => {
                        notification.classList.remove('show');
                    }, 3000);
                }
            }
        }
        
        // Function to add note to DOM
        function addNoteToDOM(noteData) {
            const notesContainer = document.querySelector('.notes-list');
            if (!notesContainer) {
                console.error('Notes container not found');
                return;
            }

            const noteItem = document.createElement('div');
            noteItem.className = 'note-item';
            noteItem.setAttribute('data-note-id', noteData.id);
            
            // Create preview (first 80 characters)
            const preview = noteData.content.substring(0, 80) + (noteData.content.length > 80 ? '...' : '');
            
            // Build topic badge HTML
            const topicBadgeHTML = noteData.topic ? 
                `<div class="note-topic-badge">${getTopicText(noteData.topic)}</div>` : '';
            
            noteItem.innerHTML = `
                <div class="note-header">
                    <span class="note-title">${noteData.title}</span>
                    <span class="note-date">${noteData.date}${noteData.isEdited ? ' (Edited)' : ''}</span>
                </div>
                ${topicBadgeHTML}
                <div class="note-preview">${preview}</div>
                <div class="note-actions">
                    <button class="edit-note" title="Edit"><i class="fas fa-edit"></i></button>
                    <button class="delete-note" title="Delete"><i class="fas fa-trash-alt"></i></button>
                </div>
                <div class="note-full-content" style="display: none;">${noteData.content}</div>
            `;
            
            // Add event listeners
            setupNoteEventListeners(noteItem, noteData.id);
            
            // Add to the top of the list (after sample notes)
            const firstUserNote = notesContainer.querySelector('.note-item:not([data-note-id="sample_note_1"]):not([data-note-id="sample_note_2"])');
            if (firstUserNote) {
                notesContainer.insertBefore(noteItem, firstUserNote);
            } else {
                notesContainer.appendChild(noteItem);
            }
            
            console.log('Added note to DOM:', noteData.title);
        }
        
        // Function to setup event listeners for a note
        function setupNoteEventListeners(noteItem, noteId) {
            const editBtn = noteItem.querySelector('.edit-note');
            const deleteBtn = noteItem.querySelector('.delete-note');
            
            if (editBtn) {
                editBtn.addEventListener('click', function() {
                    editNote(noteId, noteItem);
                });
            }
            
            if (deleteBtn) {
                deleteBtn.addEventListener('click', function() {
                    deleteNote(noteId, noteItem);
                });
            }
        }
        
        // Function to edit note
        function editNote(noteId, noteItem) {
            console.log('Editing note:', noteId);
            window.currentlyEditingNoteId = noteId;
            
            const notesArea = document.getElementById('notes-area');
            const topicSelector = document.getElementById('note-topic-selector');
            const saveBtn = document.getElementById('save-note-btn');
            const cancelBtn = document.getElementById('cancel-edit-btn');
            
            if (!notesArea || !topicSelector || !saveBtn) {
                console.error('Required elements not found');
                return;
            }
            
            // Find note data
            if (noteId.startsWith('sample_')) {
                // Handle sample notes
                const fullContent = noteItem.querySelector('.note-full-content').textContent;
                const noteTitle = noteItem.querySelector('.note-title').textContent;
                
                notesArea.value = fullContent;
                
                // Set topic selector based on title
                if (noteTitle.includes('Basics')) {
                    topicSelector.value = 'python-basics';
                } else if (noteTitle.includes('Functions')) {
                    topicSelector.value = 'functions';
                } else {
                    topicSelector.value = '';
                }
            } else {
                // Handle user notes
                const noteData = notesStorage.find(note => note.id === noteId);
                if (noteData) {
                    notesArea.value = noteData.content;
                    topicSelector.value = noteData.topic || '';
                }
            }
            
            // Update UI
            saveBtn.textContent = 'Update';
            if (cancelBtn) cancelBtn.style.display = 'flex';
            
            // Highlight the edited note
            resetNoteHighlights();
            noteItem.style.border = '2px solid #6a4c93';
            noteItem.style.backgroundColor = '#f8f4ff';
            
            // Scroll to editor
            notesArea.scrollIntoView({ behavior: 'smooth' });
            notesArea.focus();
        }
        
        // Function to delete note
        function deleteNote(noteId, noteItem) {
            if (confirm('Are you sure you want to delete this note?')) {
                console.log('Deleting note:', noteId);
                
                // Remove from storage if it's a user note
                if (!noteId.startsWith('sample_')) {
                    notesStorage = notesStorage.filter(note => note.id !== noteId);
                    saveNotesToStorage();
                }
                
                // Remove from DOM
                noteItem.remove();
                
                // Exit edit mode if this note was being edited
                if (window.currentlyEditingNoteId === noteId) {
                    resetEditMode();
                }
                
                updateNotesCount();
            }
        }
        
        // Function to load saved notes
        function loadSavedNotes() {
            console.log('Loading saved notes:', notesStorage.length, 'notes found');
            const notesContainer = document.querySelector('.notes-list');
            
            if (!notesContainer) {
                console.error('Notes container not found');
                return;
            }
            
            // Clear existing user notes (keep sample notes)
            const existingNotes = notesContainer.querySelectorAll('.note-item:not([data-note-id="sample_note_1"]):not([data-note-id="sample_note_2"])');
            existingNotes.forEach(note => note.remove());
            
            // Load notes from storage
            notesStorage.forEach(note => {
                addNoteToDOM(note);
            });
            
            updateNotesCount();
        }
        
        // Helper function to update topic badge
        function updateTopicBadge(noteItem, topicValue, topicText) {
            let topicBadge = noteItem.querySelector('.note-topic-badge');
            if (topicValue) {
                if (!topicBadge) {
                    topicBadge = document.createElement('div');
                    topicBadge.className = 'note-topic-badge';
                    noteItem.querySelector('.note-header').after(topicBadge);
                }
                topicBadge.textContent = topicText;
            } else if (topicBadge) {
                topicBadge.remove();
            }
        }
        
        // Re-initialize all sample notes with proper event listeners
        function initializeSampleNotes() {
            console.log('Re-initializing sample notes...');
            const sampleNotes = document.querySelectorAll('.note-item[data-note-id^="sample_"]');
            
            sampleNotes.forEach(noteItem => {
                const editBtn = noteItem.querySelector('.edit-note');
                const deleteBtn = noteItem.querySelector('.delete-note');
                const noteId = noteItem.getAttribute('data-note-id');
                
                if (editBtn) {
                    // Remove existing event listeners by cloning
                    const newEditBtn = editBtn.cloneNode(true);
                    editBtn.parentNode.replaceChild(newEditBtn, editBtn);
                    
                    newEditBtn.addEventListener('click', function() {
                        editNote(noteId, noteItem);
                    });
                }
                
                if (deleteBtn) {
                    // Remove existing event listeners by cloning
                    const newDeleteBtn = deleteBtn.cloneNode(true);
                    deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);
                    
                    newDeleteBtn.addEventListener('click', function() {
                        deleteNote(noteId, noteItem);
                    });
                }
            });
            
            console.log('Sample notes re-initialized:', sampleNotes.length);
        }
        
        // Initialize sample notes
        initializeSampleNotes();
        
        // Setup button event listeners
        const newNoteBtn = document.getElementById('new-note-btn');
        const saveNoteBtn = document.getElementById('save-note-btn');
        const notesArea = document.getElementById('notes-area');
        
        // New note button
        if (newNoteBtn) {
            // Remove existing listener and add new one
            const newNewNoteBtn = newNoteBtn.cloneNode(true);
            newNoteBtn.parentNode.replaceChild(newNewNoteBtn, newNoteBtn);
            
            newNewNoteBtn.addEventListener('click', function() {
                console.log('New note button clicked');
                resetEditMode();
                const notesArea = document.getElementById('notes-area');
                if (notesArea) notesArea.focus();
            });
        }
        
        // Save note button
        if (saveNoteBtn) {
            // Remove existing listener and add new one
            const newSaveNoteBtn = saveNoteBtn.cloneNode(true);
            saveNoteBtn.parentNode.replaceChild(newSaveNoteBtn, saveNoteBtn);
            
            newSaveNoteBtn.addEventListener('click', function() {
                console.log('Save note button clicked');
                const noteContent = document.getElementById('notes-area').value.trim();
                const topicSelect = document.getElementById('note-topic-selector');
                const topicValue = topicSelect.value;
                const topicText = topicValue ? getTopicText(topicValue) : 'Uncategorized';
                
                if (!noteContent) {
                    alert('Please enter note content!');
                    return;
                }
                
                const now = new Date();
                const dateStr = now.toISOString().split('T')[0]; // YYYY-MM-DD
                
                if (window.currentlyEditingNoteId) {
                    // Update existing note
                    console.log('Updating existing note:', window.currentlyEditingNoteId);
                    
                    if (window.currentlyEditingNoteId.startsWith('sample_')) {
                        // Handle sample note editing
                        const noteItem = document.querySelector(`.note-item[data-note-id="${window.currentlyEditingNoteId}"]`);
                        if (noteItem) {
                            noteItem.querySelector('.note-title').textContent = topicText;
                            noteItem.querySelector('.note-date').textContent = dateStr + ' (Edited)';
                            noteItem.querySelector('.note-preview').textContent = 
                                noteContent.substring(0, 80) + (noteContent.length > 80 ? '...' : '');
                            noteItem.querySelector('.note-full-content').textContent = noteContent;
                            
                            // Update topic badge
                            updateTopicBadge(noteItem, topicValue, topicText);
                            
                            // Visual feedback
                            noteItem.style.backgroundColor = '#f0f7ff';
                            setTimeout(() => {
                                noteItem.style.backgroundColor = '';
                                noteItem.style.transition = 'background-color 1s ease';
                            }, 100);
                        }
                    } else {
                        // Handle user note editing
                        const noteIndex = notesStorage.findIndex(note => note.id === window.currentlyEditingNoteId);
                        if (noteIndex !== -1) {
                            notesStorage[noteIndex].content = noteContent;
                            notesStorage[noteIndex].topic = topicValue;
                            notesStorage[noteIndex].title = topicText;
                            notesStorage[noteIndex].date = dateStr;
                            notesStorage[noteIndex].isEdited = true;
                            
                            saveNotesToStorage();
                            
                            // Update DOM
                            const noteItem = document.querySelector(`.note-item[data-note-id="${window.currentlyEditingNoteId}"]`);
                            if (noteItem) {
                                noteItem.querySelector('.note-title').textContent = topicText;
                                noteItem.querySelector('.note-date').textContent = dateStr + ' (Edited)';
                                noteItem.querySelector('.note-preview').textContent = 
                                    noteContent.substring(0, 80) + (noteContent.length > 80 ? '...' : '');
                                noteItem.querySelector('.note-full-content').textContent = noteContent;
                                
                                // Update topic badge
                                updateTopicBadge(noteItem, topicValue, topicText);
                                
                                // Visual feedback
                                noteItem.style.backgroundColor = '#f0f7ff';
                                setTimeout(() => {
                                    noteItem.style.backgroundColor = '';
                                    noteItem.style.transition = 'background-color 1s ease';
                                }, 100);
                            }
                        }
                    }
                    
                    // showNotification('Note updated successfully!'); - removed notification
                } else {
                    // Create new note
                    console.log('Creating new note');
                    const noteData = {
                        id: 'note_' + Date.now(),
                        title: topicText,
                        content: noteContent,
                        topic: topicValue,
                        date: dateStr,
                        isEdited: false
                    };
                    
                    notesStorage.unshift(noteData); // Add to beginning
                    saveNotesToStorage();
                    addNoteToDOM(noteData);
                    updateNotesCount();
                }
                
                // Reset form
                resetEditMode();
            });
        }
        
        // Add cancel button if it doesn't exist
        const notesToolbar = document.querySelector('.notes-toolbar');
        if (notesToolbar && !document.getElementById('cancel-edit-btn')) {
            notesToolbar.insertAdjacentHTML('beforeend', `
                <button id="cancel-edit-btn" class="note-btn" style="display: none;">
                    <i class="fas fa-times"></i> Cancel
                </button>
            `);
            
            // Add event listener for cancel button
            const cancelBtn = document.getElementById('cancel-edit-btn');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', function() {
                    resetEditMode();
                });
            }
        }
        
        // Make notes-area automatically resizable
        if (notesArea) {
            notesArea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
        }
        
        // Load saved notes from localStorage
        loadSavedNotes();
        
        console.log('Complete Notes Fix: Initialization completed successfully');
        
    }, 2000); // Wait 2 seconds for other scripts to load
}); 