// Python Knowledge Graph Data
const pythonEntities = [
  { id: 'e1', type: 'concept', name: 'Variables', description: 'Named references to objects in memory' },
  { id: 'e2', type: 'concept', name: 'Data Types', description: 'Categories of values in Python' },
  { id: 'e3', type: 'datatype', name: 'int', description: 'Integer numbers' },
  { id: 'e4', type: 'datatype', name: 'float', description: 'Floating-point numbers' },
  { id: 'e5', type: 'datatype', name: 'str', description: 'Text sequences' },
  { id: 'e6', type: 'datatype', name: 'bool', description: 'Boolean values (True/False)' },
  { id: 'e7', type: 'datatype', name: 'list', description: 'Ordered, mutable collections' },
  { id: 'e8', type: 'datatype', name: 'dict', description: 'Key-value mappings' },
  { id: 'e9', type: 'concept', name: 'Control Flow', description: 'Structures controlling execution order' },
  { id: 'e10', type: 'structure', name: 'if-else', description: 'Conditional execution' },
  { id: 'e11', type: 'structure', name: 'for loop', description: 'Iteration over sequences' },
  { id: 'e12', type: 'structure', name: 'while loop', description: 'Conditional iteration' },
  { id: 'e13', type: 'concept', name: 'Functions', description: 'Reusable code blocks' },
  { id: 'e14', type: 'concept', name: 'Parameters', description: 'Inputs to functions' },
  { id: 'e15', type: 'concept', name: 'Return Values', description: 'Outputs from functions' }
];

const pythonTriplets = [
  { id: 't1', subject: 'e1', predicate: 'stores', object: 'e2', description: 'Variables store data of specific types' },
  { id: 't2', subject: 'e2', predicate: 'includes', object: 'e3', description: 'Data types include integers' },
  { id: 't3', subject: 'e2', predicate: 'includes', object: 'e4', description: 'Data types include floats' },
  { id: 't4', subject: 'e2', predicate: 'includes', object: 'e5', description: 'Data types include strings' },
  { id: 't5', subject: 'e2', predicate: 'includes', object: 'e6', description: 'Data types include booleans' },
  { id: 't6', subject: 'e2', predicate: 'includes', object: 'e7', description: 'Data types include lists' },
  { id: 't7', subject: 'e2', predicate: 'includes', object: 'e8', description: 'Data types include dictionaries' },
  { id: 't8', subject: 'e9', predicate: 'uses', object: 'e10', description: 'Control flow uses if-else statements' },
  { id: 't9', subject: 'e9', predicate: 'uses', object: 'e11', description: 'Control flow uses for loops' },
  { id: 't10', subject: 'e9', predicate: 'uses', object: 'e12', description: 'Control flow uses while loops' },
  { id: 't11', subject: 'e13', predicate: 'has', object: 'e14', description: 'Functions have parameters' },
  { id: 't12', subject: 'e13', predicate: 'provides', object: 'e15', description: 'Functions provide return values' },
  { id: 't13', subject: 'e10', predicate: 'evaluates', object: 'e6', description: 'If-else statements evaluate boolean expressions' },
  { id: 't14', subject: 'e11', predicate: 'iterates', object: 'e7', description: 'For loops iterate over sequences like lists' }
];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
  // Initialize the knowledge graph with a delay to ensure DOM is fully loaded
  setTimeout(() => {
    initializeGraph();
  }, 100);
  
  // Set up chatbot event listeners
  console.log('DOM content loaded, setting up chatbot');
  setupChatbot();
});

function initializeGraph() {
  // Update the count display
  document.getElementById('nodeCount') && (document.getElementById('nodeCount').textContent = pythonEntities.length);
  document.getElementById('edgeCount') && (document.getElementById('edgeCount').textContent = pythonTriplets.length);
  
  // Check if D3.js is loaded
  if (typeof d3 === 'undefined') {
    console.error('D3.js is not loaded. Graph visualization requires D3.js.');
    document.getElementById('graph').innerHTML = 'D3.js is required for graph visualization.';
    return;
  }
  
  // Set up the visualization area
  const width = document.getElementById('graph').clientWidth;
  const height = window.innerHeight * 0.7; // Use 70% of window height for better vertical space
  
  // Clear previous visualization if any
  d3.select('#graph').html('');
  
  // Create SVG container with zoom functionality
  const svg = d3.select('#graph').append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet');
  
  // Create a background rect for zoom area
  svg.append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'rgba(245, 247, 250, 0.6)');
    
  // Add zoom capabilities
  const zoomG = svg.append('g');
  
  const zoom = d3.zoom()
    .scaleExtent([0.3, 3])
    .on('zoom', (event) => {
      zoomG.attr('transform', event.transform);
    });
    
  svg.call(zoom);
  
  // Initial zoom out to show the whole graph
  svg.call(zoom.transform, d3.zoomIdentity.scale(0.8).translate(width/8, height/8));
  
  // Create graph data
  const nodes = pythonEntities.map(entity => ({
    id: entity.id,
    name: entity.name,
    type: entity.type,
    description: entity.description
  }));
  
  const links = pythonTriplets.map(triplet => ({
    id: triplet.id,
    source: triplet.subject,
    target: triplet.object,
    predicate: triplet.predicate,
    description: triplet.description
  }));
  
  // Create force simulation
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(180))
    .force('charge', d3.forceManyBody().strength(-600))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(35))
    .alphaDecay(0.01); // Slower cooling to allow nodes to find better positions
  
  // Define color scale for node types
  const typeColors = {
    'concept': '#3498db',   // --concept-color from CSS
    'datatype': '#2ecc71',  // --datatype-color from CSS
    'structure': '#f39c12'  // --structure-color from CSS
  };
  
  // Create links as curved paths
  const link = zoomG.append('g')
    .selectAll('path')
    .data(links)
    .enter().append('path')
    .attr('stroke', d => {
      // Use different colors based on the predicate type - using our color palette
      const predicateColors = {
        'includes': '#3498db',  // accent-color (blue)
        'has': '#e74c3c',       // danger-color (red)
        'uses': '#3a506b',      // primary-light (dark blue)
        'provides': '#1abc9c',  // secondary-color (teal)
        'evaluates': '#f39c12', // warning-color (orange) 
        'iterates': '#2ecc71',  // success-color (green)
        'stores': '#2980b9'     // accent-hover (darker blue)
      };
      return predicateColors[d.predicate] || '#5d6778'; // secondary-text as default
    })
    .attr('stroke-opacity', 0.7)
    .attr('stroke-width', 1.5)
    .attr('fill', 'none');
  
  // Create link labels
  const linkText = zoomG.append('g')
    .selectAll('text')
    .data(links)
    .enter().append('text')
    .text(d => d.predicate)
    .attr('font-size', '10px')
    .attr('font-weight', 'bold')
    .attr('text-anchor', 'middle')
    .attr('dy', -5)
    .attr('fill', '#2c3e50')  // primary-text color
    .attr('stroke', '#ffffff') // light-text color
    .attr('stroke-width', 0.3)
    .attr('paint-order', 'stroke');
  
  // Create nodes
  const node = zoomG.append('g')
    .selectAll('circle')
    .data(nodes)
    .enter().append('circle')
    .attr('r', 8)
    .attr('fill', d => typeColors[d.type] || '#999')
    .attr('stroke', '#ffffff')
    .attr('stroke-width', 1.5)
    .call(drag(simulation));
  
  // Create node labels
  const nodeText = zoomG.append('g')
    .selectAll('text')
    .data(nodes)
    .enter().append('text')
    .text(d => d.name)
    .attr('font-size', '11px')
    .attr('text-anchor', 'middle')
    .attr('dy', 18);
  
  // Add tooltips on hover
  node.append('title')
    .text(d => `${d.name}: ${d.description}`);
  
  // Update positions on each simulation tick
  simulation.on('tick', () => {
    link
      .attr('d', d => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const dr = Math.sqrt(dx * dx + dy * dy) * 1.5; // Controls the curve
        return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
      });
    
    linkText
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2);
    
    node
      .attr('cx', d => d.x = Math.max(30, Math.min(width - 30, d.x)))
      .attr('cy', d => d.y = Math.max(30, Math.min(height - 30, d.y)));
    
    nodeText
      .attr('x', d => d.x)
      .attr('y', d => d.y);
  });
  
  // Dragging functionality
  function drag(simulation) {
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }
    
    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }
    
    return d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  }
}

// Chatbot Functionality
function setupChatbot() {
  console.log('Setting up chatbot...');
  
  // Elements
  const chatbotContainer = document.getElementById('chatbotContainer');
  const closeChatbotBtn = document.getElementById('closeChatbot');
  const chatInput = document.getElementById('chatInput');
  const sendMessageBtn = document.getElementById('sendMessage');
  const chatMessages = document.getElementById('chatMessages');
  
  console.log('Chatbot elements:', {
    chatbotContainer: !!chatbotContainer,
    closeChatbotBtn: !!closeChatbotBtn,
    chatInput: !!chatInput,
    sendMessageBtn: !!sendMessageBtn,
    chatMessages: !!chatMessages
  });
  
  if (!chatbotContainer || !chatInput || !sendMessageBtn || !chatMessages) {
    console.error('Chatbot elements not found in the DOM');
    return;
  }
  
  // Event listeners
  if (closeChatbotBtn) {
    closeChatbotBtn.addEventListener('click', () => {
      chatbotContainer.classList.remove('show');
    });
  }
  
  // Send message on button click
  sendMessageBtn.addEventListener('click', sendUserMessage);
  
  // Send message on Enter key
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendUserMessage();
    }
  });
  
  // Focus input when chatbot is opened
  if (document.getElementById('openChatbot')) {
    document.getElementById('openChatbot').addEventListener('click', () => {
      chatbotContainer.classList.add('show');
      chatInput.focus();
      // Scroll to the bottom of the chat
      chatMessages.scrollTop = chatMessages.scrollHeight;
    });
  }
  
  // Initial welcome message
  setTimeout(() => {
    addMessageToChat('bot', '<div class="answer-box"><div class="answer-title">Welcome</div><div class="answer-content"><div class="step-detail"><p>Hello! I\'m your Python learning assistant. How can I help you today?</p></div></div></div>');
  }, 500);
}

function sendUserMessage() {
  const chatInput = document.getElementById('chatInput');
  const chatMessages = document.getElementById('chatMessages');
  
  // Get user input
  const userMessage = chatInput.value.trim();
  
  // Don't send empty messages
  if (!userMessage) return;
  
  // Add user message to chat
  addMessageToChat('user', userMessage);
  
  // Clear input field
  chatInput.value = '';
  
  // Show typing indicator
  const typingIndicator = document.createElement('div');
  typingIndicator.className = 'message bot typing';
  typingIndicator.innerHTML = '<div class="typing-animation"><span></span><span></span><span></span></div>';
  chatMessages.appendChild(typingIndicator);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  // Get response from chatbot
  fetchChatbotResponse(userMessage)
    .then(response => {
      // Remove typing indicator
      chatMessages.removeChild(typingIndicator);
      
      // Add bot response to chat
      addMessageToChat('bot', response.response, response.question_type);
    })
    .catch(error => {
      console.error('Error fetching chatbot response:', error);
      
      // Remove typing indicator
      chatMessages.removeChild(typingIndicator);
      
      // Show error message
      addMessageToChat('bot', 
        '<div class="answer-box"><div class="answer-title">Error</div><div class="answer-content"><div class="step-detail"><p>Sorry, there was an error processing your request. Please try again later.</p></div></div></div>');
    });
}

function addMessageToChat(sender, message, question_type = null) {
  const chatMessages = document.getElementById('chatMessages');
  
  // Create message element
  const messageElement = document.createElement('div');
  messageElement.className = `message ${sender}`;
  
  // If it's a bot message with a question type, add a visual indicator
  if (sender === 'bot' && question_type) {
    messageElement.classList.add(`question-type-${question_type.toLowerCase()}`);
    
    // Add a small badge indicating the question type
    const typeBadge = document.createElement('div');
    typeBadge.className = 'question-type-badge';
    typeBadge.textContent = question_type === 'DIRECT' ? 'QUICK' : 'DETAILED';
    messageElement.appendChild(typeBadge);
  }
  
  // If it's a user message, just use the text
  // If it's a bot message, it might be HTML
  if (sender === 'user') {
    messageElement.textContent = message;
    
    // Store the message in a data attribute for later use
    messageElement.setAttribute('data-message', message);
  } else {
    messageElement.innerHTML = message;
    
    // If this is a DIRECT answer, add a button to get a more detailed response
    if (question_type === 'DIRECT') {
      const detailButton = document.createElement('button');
      detailButton.className = 'get-detailed-btn';
      detailButton.innerHTML = '<i class="fas fa-book"></i> Get Detailed Python Guide';
      
      // Add click event to get a detailed response
      detailButton.addEventListener('click', function() {
        // Get the user's question from the previous message
        const userMessage = messageElement.previousElementSibling.getAttribute('data-message');
        if (userMessage) {
          // Request detailed answer
          requestDetailedAnswer(userMessage);
          
          // Disable the button to prevent multiple requests
          this.disabled = true;
          this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading Detailed Guide...';
        }
      });
      
      messageElement.appendChild(detailButton);
    }
    
    // Check if the message contains code blocks
    if (sender === 'bot' && message.includes('<pre><code')) {
      // Add a "Run Code" button for each code block
      setTimeout(() => {
        const codeBlocks = messageElement.querySelectorAll('pre code');
        codeBlocks.forEach((codeBlock, index) => {
          // Get the code
          const code = codeBlock.textContent;
          
          // Create a button container
          const buttonContainer = document.createElement('div');
          buttonContainer.className = 'code-actions';
          
          // Create a "Run Code" button
          const runButton = document.createElement('button');
          runButton.className = 'run-code-btn';
          runButton.innerHTML = '<i class="fas fa-play"></i> Run Code';
          runButton.addEventListener('click', async function() {
            // Change button state
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
            
            // Execute the code
            const result = await executeCode(code);
            
            // Create or update the output container
            let outputContainer = codeBlock.parentNode.nextElementSibling;
            if (!outputContainer || !outputContainer.classList.contains('code-output')) {
              outputContainer = document.createElement('div');
              outputContainer.className = 'code-output';
              codeBlock.parentNode.insertAdjacentElement('afterend', outputContainer);
            }
            
            // Display the result
            if (result.success) {
              outputContainer.innerHTML = `
                <div class="output-header">Output:</div>
                <pre class="output-content">${result.output || '(No output)'}</pre>
              `;
            } else {
              outputContainer.innerHTML = `
                <div class="output-header error">Error:</div>
                <pre class="output-content error">${result.error || 'An unknown error occurred'}</pre>
              `;
            }
            
            // Restore button state
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-play"></i> Run Code';
          });
          
          // Add the button to the container
          buttonContainer.appendChild(runButton);
          
          // Add the container after the code block
          codeBlock.parentNode.insertAdjacentElement('afterend', buttonContainer);
        });
      }, 0);
    }
  }
  
  // Add message to chat
  chatMessages.appendChild(messageElement);
  
  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Function to request a detailed answer
async function requestDetailedAnswer(message) {
  const chatMessages = document.getElementById('chatMessages');
  
  // Show typing indicator
  const typingIndicator = document.createElement('div');
  typingIndicator.className = 'message bot typing';
  typingIndicator.innerHTML = '<div class="typing-animation"><span></span><span></span><span></span></div>';
  chatMessages.appendChild(typingIndicator);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  try {
    // Call the detailed chat endpoint
    const response = await fetch('/api/detailed_chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Remove typing indicator
    chatMessages.removeChild(typingIndicator);
    
    // Add bot response to chat
    addMessageToChat('bot', data.response, data.question_type);
  } catch (error) {
    console.error('Error fetching detailed response:', error);
    
    // Remove typing indicator
    chatMessages.removeChild(typingIndicator);
    
    // Show error message
    addMessageToChat('bot', 
      '<div class="answer-box"><div class="answer-title">Error</div><div class="answer-content"><div class="step-detail"><p>Sorry, there was an error getting a detailed answer. Please try again later.</p></div></div></div>');
  }
}

// Function to generate a basic response based on the knowledge graph
function generateBasicResponse(message) {
  message = message.toLowerCase();
  
  // Check for mentions of entities in our knowledge graph
  for (const entity of pythonEntities) {
    if (message.includes(entity.name.toLowerCase())) {
      return `${entity.name}: ${entity.description}. What else would you like to know about Python?`;
    }
  }
  
  // Check for general Python-related queries
  if (message.includes('python')) {
    return "Python is a high-level, interpreted programming language known for its readability and versatility. It supports multiple programming paradigms and has a comprehensive standard library.";
  }
  
  if (message.includes('variable') || message.includes('variables')) {
    return "In Python, variables are names that refer to values. You create a variable by assigning a value to it using the equals sign (=). For example: x = 10";
  }
  
  if (message.includes('function') || message.includes('functions')) {
    return "Python functions are defined using the 'def' keyword. They can take parameters and return values. For example: def greet(name): return f'Hello, {name}!'";
  }
  
  if (message.includes('loop') || message.includes('loops')) {
    return "Python has two main types of loops: 'for' loops for iterating over sequences, and 'while' loops for repeating code while a condition is true.";
  }
  
  // Default response
  return "I'm here to help with Python questions. You can ask me about variables, data types, functions, or other Python concepts shown in the knowledge graph.";
}

// New functions for code analysis and problem identification

// Function to analyze code and identify problems
async function analyzeCode(code, errorMessage = null) {
  try {
    const response = await fetch('/api/analyze_code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        code: code,
        error_message: errorMessage 
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error analyzing code:', error);
    return {
      problem_type: 'analysis_error',
      problem_details: {
        description: 'Failed to analyze code',
        error: error.message
      },
      analysis_method: 'error'
    };
  }
}

// Function to classify a natural language query
async function classifyQuery(query) {
  try {
    const response = await fetch('/api/classify_query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error classifying query:', error);
    return {
      query_type: 'DIRECT', // Default to direct for errors
      analysis_method: 'error',
      error: error.message
    };
  }
}

// Extract code from a message
function extractCodeFromMessage(message) {
  // Check for code blocks with triple backticks
  const codeBlockRegex = /```(?:python)?([\s\S]*?)```/g;
  const matches = [...message.matchAll(codeBlockRegex)];
  
  if (matches.length > 0) {
    return matches[0][1].trim();
  }
  
  // If no code blocks found, check for indented code
  const lines = message.split('\n');
  const indentedLines = lines.filter(line => line.startsWith('    ') || line.startsWith('\t'));
  
  if (indentedLines.length > 0) {
    return indentedLines.join('\n');
  }
  
  return null;
}

// Extract error message from a message
function extractErrorMessage(message) {
  // Look for common error patterns
  const errorPatterns = [
    /Error:([\s\S]*?)(?:\n\n|$)/i,
    /Exception:([\s\S]*?)(?:\n\n|$)/i,
    /Traceback \(most recent call last\):([\s\S]*?)(?:\n\n|$)/i
  ];
  
  for (const pattern of errorPatterns) {
    const match = message.match(pattern);
    if (match) {
      return match[0];
    }
  }
  
  return null;
}

// Function to execute code and show the result
async function executeCode(code) {
  try {
    const response = await fetch('/api/execute_code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ code })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error executing code:', error);
    return {
      success: false,
      output: '',
      error: error.message
    };
  }
}

// Update fetchChatbotResponse to use the problem identification
async function fetchChatbotResponse(message) {
  try {
    // First check if the message contains code
    const code = extractCodeFromMessage(message);
    const errorMessage = extractErrorMessage(message);
    
    // If code is found, analyze it
    if (code) {
      const analysis = await analyzeCode(code, errorMessage);
      
      // If problem was identified, include it in the response
      if (analysis.problem_type !== 'unknown' && analysis.problem_type !== 'analysis_error') {
        // Send the analysis to our regular chat endpoint
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ 
            message,
            code_analysis: analysis 
          })
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
      }
    }
    
    // If no code or problem couldn't be identified, classify the query
    const classification = await classifyQuery(message);
    
    // Use the regular chat endpoint with the classification
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        message,
        query_classification: classification 
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching response from API:', error);
    
    // Fallback to a basic response
    return {
      response: generateBasicResponse(message),
      question_type: 'DIRECT'
    };
  }
}

// 新增：复制代码和运行代码功能
function copyCode(button) {
  const codeBlock = button.closest('.code-snippet').querySelector('pre code');
  const codeText = codeBlock.textContent;
  
  navigator.clipboard.writeText(codeText).then(() => {
    // 更新按钮文本
    const originalHTML = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check"></i> Copied';
    button.style.background = '#27ae60';
    
    // 2秒后恢复原状
    setTimeout(() => {
      button.innerHTML = originalHTML;
      button.style.background = 'rgba(108, 99, 255, 0.8)';
    }, 2000);
    
    // 显示toast提示
    showToast('Code copied to clipboard! 📋', 'success');
  }).catch(err => {
    console.error('Copy failed:', err);
    showToast('Copy failed, please select code manually', 'error');
  });
}

function runCode(button) {
  const codeBlock = button.closest('.code-snippet').querySelector('pre code');
  const codeText = codeBlock.textContent;
  const outputDiv = button.closest('.code-snippet').querySelector('.code-output');
  const outputContent = outputDiv.querySelector('.output-content');
  const outputHeader = outputDiv.querySelector('.output-header');
  
  // 显示输出区域
  outputDiv.style.display = 'block';
  outputContent.textContent = 'Running code...';
  outputHeader.classList.remove('error');
  outputContent.classList.remove('error');
  
  // 更新按钮状态
  const originalHTML = button.innerHTML;
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running';
  button.disabled = true;
  
  // 发送代码执行请求
  fetch('/api/execute_code', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      code: codeText
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      outputContent.textContent = data.output || 'Code executed successfully (no output)';
      showToast('Code executed successfully! ✅', 'success');
    } else {
      outputContent.textContent = data.error || 'An error occurred';
      outputHeader.classList.add('error');
      outputContent.classList.add('error');
      showToast('Code execution failed ❌', 'error');
    }
  })
  .catch(error => {
    console.error('Execution error:', error);
    outputContent.textContent = 'Network error: Could not execute code';
    outputHeader.classList.add('error');
    outputContent.classList.add('error');
    showToast('Network error occurred', 'error');
  })
  .finally(() => {
    // 恢复按钮状态
    button.innerHTML = originalHTML;
    button.disabled = false;
  });
}

function showToast(message, type = 'info') {
  // 创建toast元素
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  
  // 添加样式
  Object.assign(toast.style, {
    position: 'fixed',
    top: '20px',
    right: '20px',
    padding: '12px 16px',
    borderRadius: '8px',
    color: 'white',
    fontSize: '14px',
    fontWeight: '500',
    zIndex: '10000',
    opacity: '0',
    transform: 'translateY(-20px)',
    transition: 'all 0.3s ease'
  });
  
  // 设置类型特定样式
  switch(type) {
    case 'success':
      toast.style.background = 'linear-gradient(135deg, #27ae60, #2ecc71)';
      break;
    case 'error':
      toast.style.background = 'linear-gradient(135deg, #e74c3c, #c0392b)';
      break;
    case 'info':
    default:
      toast.style.background = 'linear-gradient(135deg, #3498db, #2980b9)';
      break;
  }
  
  // 添加到页面
  document.body.appendChild(toast);
  
  // 显示动画
  setTimeout(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  }, 100);
  
  // 3秒后隐藏
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-20px)';
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }, 3000);
}

// 添加CSS动画（如果不存在）
if (!document.querySelector('#toast-styles')) {
  const style = document.createElement('style');
  style.id = 'toast-styles';
  style.textContent = `
    @keyframes slideInRight {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes slideOutRight {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }
    
    .toast-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    
    .toast-message {
      flex: 1;
      font-weight: 500;
    }
    
    .toast-close {
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      padding: 0;
      font-size: 14px;
      opacity: 0.8;
      transition: opacity 0.2s;
    }
    
    .toast-close:hover {
      opacity: 1;
    }
  `;
  document.head.appendChild(style);
}

// 增强现有的executeCode函数（如果需要）
if (typeof executeCode === 'undefined') {
  async function executeCode(code) {
    try {
      const response = await fetch('/api/execute_code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: code
        })
      });
      
      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Code execution error:', error);
      return {
        success: false,
        error: '网络连接错误'
      };
    }
  }
} 