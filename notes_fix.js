// Study Notes Fix Script
// This script fixes the Study Notes functionality issues

document.addEventListener('DOMContentLoaded', function() {
    console.log('Notes fix script loaded');
    
    // Wait for the main script to initialize
    setTimeout(function() {
        // Check if the notes functionality variables exist
        if (typeof window.currentlyEditingNoteId === 'undefined') {
            window.currentlyEditingNoteId = null;
        }
        
        // Function to save note to server
        async function saveNote(noteData) {
            try {
                const method = noteData.id ? 'PUT' : 'POST';
                const url = noteData.id ? `/api/notes/${noteData.id}` : '/api/notes';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        title: noteData.title,
                        content: noteData.content,
                        topic: noteData.topic
                    })
                });
                
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to save note');
                }
                
                return data;
            } catch (error) {
                console.error('Error saving note:', error);
                throw error;
            }
        }
        
        // Function to load notes from server
        async function loadNotes() {
            try {
                const response = await fetch('/api/notes', {
                    method: 'GET',
                    credentials: 'include'
                });
                
                // Return empty array for unauthorized users
                if (response.status === 401) {
                    return [];
                }
                
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to load notes');
                }
                
                return data.notes;
            } catch (error) {
                console.error('Error loading notes:', error);
                return [];
            }
        }
        
        // Function to delete note from server
        async function deleteNote(noteId) {
            try {
                const response = await fetch(`/api/notes/${noteId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to delete note');
                }
                
                return true;
            } catch (error) {
                console.error('Error deleting note:', error);
                return false;
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
                    <span class="note-date">${new Date(noteData.updated_at || noteData.created_at).toLocaleString()}</span>
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
            const editBtn = noteItem.querySelector('.edit-note');
            const deleteBtn = noteItem.querySelector('.delete-note');
            
            if (editBtn) {
                editBtn.addEventListener('click', function() {
                    window.currentlyEditingNoteId = noteData.id;
                    document.getElementById('notes-area').value = noteData.content;
                    document.getElementById('note-topic-selector').value = noteData.topic || '';
                    document.getElementById('save-note-btn').textContent = 'Update';
                    
                    const cancelBtn = document.getElementById('cancel-edit-btn');
                    if (cancelBtn) cancelBtn.style.display = 'flex';
                    
                    resetNoteHighlights();
                    noteItem.style.border = '2px solid #6a4c93';
                    noteItem.style.backgroundColor = '#f8f4ff';
                    
                    document.getElementById('notes-area').scrollIntoView({ behavior: 'smooth' });
                    document.getElementById('notes-area').focus();
                });
            }
            
            if (deleteBtn) {
                deleteBtn.addEventListener('click', async function() {
                    if (confirm('Are you sure you want to delete this note?')) {
                        const success = await deleteNote(noteData.id);
                        if (success) {
                            noteItem.remove();
                            if (window.currentlyEditingNoteId === noteData.id) {
                                resetEditMode();
                            }
                            updateNotesCount();
                        }
                    }
                });
            }
            
            // Add to the top of the list
            const firstNote = notesContainer.querySelector('.note-item');
            if (firstNote) {
                notesContainer.insertBefore(noteItem, firstNote);
            } else {
                notesContainer.appendChild(noteItem);
            }
        }
        
        // Function to reset edit mode
        function resetEditMode() {
            window.currentlyEditingNoteId = null;
            document.getElementById('save-note-btn').textContent = 'Save';
            document.getElementById('notes-area').value = '';
            document.getElementById('note-topic-selector').value = '';
            
            const cancelBtn = document.getElementById('cancel-edit-btn');
            if (cancelBtn) cancelBtn.style.display = 'none';
            
            resetNoteHighlights();
        }
        
        // Function to reset note highlights
        function resetNoteHighlights() {
            const allNotes = document.querySelectorAll('.note-item');
            allNotes.forEach(note => {
                note.style.border = '1px solid #e9ecef';
                note.style.backgroundColor = '';
            });
        }
        
        // Function to update notes count
        function updateNotesCount() {
            const totalNotes = document.querySelectorAll('.note-item').length;
            const notesCountElement = document.getElementById('notes-count');
            if (notesCountElement) {
                notesCountElement.textContent = `${totalNotes} notes`;
            }
        }
        
        // Helper function to get topic text
        function getTopicText(topicValue) {
            const topicOptions = {
                'python-basics': 'Python Basics',
                'data-types': 'Data Types',
                'functions': 'Functions',
                'oop': 'OOP Concepts',
                'libraries': 'Python Libraries',
                'control-flow': 'Control Flow',
                'data-structures': 'Data Structures',
                'algorithms': 'Algorithms'
            };
            return topicOptions[topicValue] || 'Uncategorized';
        }
        
        // Initialize save button functionality
        const saveNoteBtn = document.getElementById('save-note-btn');
        if (saveNoteBtn) {
            saveNoteBtn.addEventListener('click', async function() {
                const notesArea = document.getElementById('notes-area');
                const topicSelector = document.getElementById('note-topic-selector');
                
                if (!notesArea || !topicSelector) {
                    console.error('Required elements not found');
                    return;
                }
                
                const noteContent = notesArea.value.trim();
                const topicValue = topicSelector.value;
                const topicText = getTopicText(topicValue);
                
                if (!noteContent) {
                    alert('Please enter some content for your note');
                    return;
                }
                
                try {
                    const noteData = {
                        id: window.currentlyEditingNoteId,
                        title: topicText,
                        content: noteContent,
                        topic: topicValue
                    };
                    
                    const result = await saveNote(noteData);
                    
                    if (window.currentlyEditingNoteId) {
                        // Update existing note in DOM
                        const noteItem = document.querySelector(`.note-item[data-note-id="${window.currentlyEditingNoteId}"]`);
                        if (noteItem) {
                            noteItem.remove();
                        }
                    }
                    
                    // Add new/updated note to DOM
                    noteData.id = result.note_id || window.currentlyEditingNoteId;
                    addNoteToDOM(noteData);
                    updateNotesCount();
                    resetEditMode();
                    
                } catch (error) {
                    alert('Failed to save note: ' + error.message);
                }
            });
        }
        
        // Initialize cancel button
        const cancelBtn = document.getElementById('cancel-edit-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                resetEditMode();
            });
        }
        
        // Load saved notes
        loadNotes().then(notes => {
            const notesContainer = document.querySelector('.notes-list');
            if (notesContainer) {
                notesContainer.innerHTML = ''; // Clear existing notes
                notes.forEach(note => addNoteToDOM(note));
                updateNotesCount();
            }
        });
        
    }, 1000); // Wait 1 second for main script to load
}); 