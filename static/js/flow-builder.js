/**
 * Flow Builder for Voice AI Campaign System
 * Manages the visual representation and editing of conversation flows
 */

class FlowBuilder {
    constructor(containerId, saveButtonId, flowData = null) {
        this.container = document.getElementById(containerId);
        this.saveButton = document.getElementById(saveButtonId);
        this.flowData = flowData || { steps: [] };
        this.draggedNode = null;
        this.init();
    }

    init() {
        // Render the initial flow
        this.renderFlow();

        // Set up event listeners
        this.setupEventListeners();
    }

    renderFlow() {
        if (!this.container) return;

        // Clear the container
        this.container.innerHTML = '';

        // Sort steps to ensure proper rendering order
        const steps = [...this.flowData.steps].sort((a, b) => {
            // Start with intro
            if (a.id === 'intro') return -1;
            if (b.id === 'intro') return 1;
            // End with end
            if (a.id === 'end') return 1;
            if (b.id === 'end') return -1;
            return 0;
        });

        // Create a map of steps for easy lookup
        const stepsMap = {};
        steps.forEach(step => {
            stepsMap[step.id] = step;
        });

        // Render each step
        steps.forEach(step => {
            const nodeElement = this.createNodeElement(step);
            this.container.appendChild(nodeElement);

            // Add connector if this step has a next step
            if (step.next && step.next !== 'end') {
                const connector = document.createElement('div');
                connector.className = 'flow-connector';
                this.container.appendChild(connector);
            }

            // For response nodes, add branches
            if (step.type === 'response' && step.branches) {
                const branchesContainer = document.createElement('div');
                branchesContainer.className = 'ml-8 pl-4 border-l-2 border-gray-300';

                // Add each branch
                Object.entries(step.branches).forEach(([sentiment, nextStepId]) => {
                    const nextStep = stepsMap[nextStepId];
                    if (nextStep) {
                        // Add sentiment label
                        const sentimentLabel = document.createElement('div');
                        sentimentLabel.className = 'text-sm font-medium mb-2';
                        sentimentLabel.textContent = this.formatSentiment(sentiment);
                        branchesContainer.appendChild(sentimentLabel);

                        // Add the branch node
                        const branchNode = this.createNodeElement(nextStep, true);
                        branchesContainer.appendChild(branchNode);

                        // Add connector if this branch has a next step
                        if (nextStep.next && nextStep.next !== 'end') {
                            const connector = document.createElement('div');
                            connector.className = 'flow-connector ml-4';
                            branchesContainer.appendChild(connector);
                        }
                    }
                });

                this.container.appendChild(branchesContainer);
            }
        });
    }

    createNodeElement(step, isBranch = false) {
        const node = document.createElement('div');
        node.className = `flow-node flow-node-${step.type} ${isBranch ? 'mb-4' : ''}`;
        node.dataset.id = step.id;
        node.dataset.type = step.type;
        node.draggable = true;

        // Header with step name and type
        const header = document.createElement('div');
        header.className = 'flex justify-between items-center mb-2';
        
        const title = document.createElement('h3');
        title.className = 'font-medium';
        title.textContent = step.name || step.id;
        
        const type = document.createElement('span');
        type.className = 'text-xs px-2 py-1 rounded-full bg-gray-200 text-gray-700';
        type.textContent = this.formatStepType(step.type);
        
        header.appendChild(title);
        header.appendChild(type);
        node.appendChild(header);

        // Content based on step type
        if (step.type === 'message') {
            const content = document.createElement('p');
            content.className = 'text-sm text-gray-600 mb-2';
            content.textContent = step.text || '';
            node.appendChild(content);
        } else if (step.type === 'response') {
            const content = document.createElement('p');
            content.className = 'text-sm text-gray-600 mb-2';
            content.textContent = 'Waiting for voter response...';
            node.appendChild(content);
            
            // Add branch info
            if (step.branches) {
                const branches = document.createElement('div');
                branches.className = 'text-xs text-gray-500';
                branches.textContent = `Branches: ${Object.keys(step.branches).map(b => this.formatSentiment(b)).join(', ')}`;
                node.appendChild(branches);
            }
        }

        // Actions
        const actions = document.createElement('div');
        actions.className = 'flex justify-end mt-2 space-x-2';
        
        const editBtn = document.createElement('button');
        editBtn.className = 'text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200';
        editBtn.textContent = 'Edit';
        editBtn.onclick = (e) => {
            e.stopPropagation();
            this.editNode(step);
        };
        
        actions.appendChild(editBtn);
        
        // Only allow deletion of certain nodes
        if (step.id !== 'intro' && step.id !== 'end') {
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200';
            deleteBtn.textContent = 'Delete';
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                this.deleteNode(step.id);
            };
            actions.appendChild(deleteBtn);
        }
        
        node.appendChild(actions);

        // Add drag and drop event listeners
        node.addEventListener('dragstart', (e) => this.handleDragStart(e, step));
        node.addEventListener('dragover', (e) => this.handleDragOver(e));
        node.addEventListener('drop', (e) => this.handleDrop(e, step));
        node.addEventListener('dragend', () => this.handleDragEnd());

        return node;
    }

    handleDragStart(e, step) {
        this.draggedNode = step;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', step.id);
        e.currentTarget.classList.add('opacity-50');
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    handleDrop(e, targetStep) {
        e.preventDefault();
        if (!this.draggedNode || this.draggedNode.id === targetStep.id) return;

        // Reorder the steps
        const draggedIndex = this.flowData.steps.findIndex(s => s.id === this.draggedNode.id);
        const targetIndex = this.flowData.steps.findIndex(s => s.id === targetStep.id);

        if (draggedIndex !== -1 && targetIndex !== -1) {
            const [removed] = this.flowData.steps.splice(draggedIndex, 1);
            this.flowData.steps.splice(targetIndex, 0, removed);
            this.renderFlow();
        }
    }

    handleDragEnd() {
        this.draggedNode = null;
        document.querySelectorAll('.flow-node').forEach(node => {
            node.classList.remove('opacity-50');
        });
    }

    editNode(step) {
        // Create a modal for editing the step
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'bg-white rounded-lg shadow-xl p-6 w-full max-w-lg';
        
        // Modal header
        const header = document.createElement('div');
        header.className = 'flex justify-between items-center mb-4';
        
        const title = document.createElement('h2');
        title.className = 'text-xl font-bold';
        title.textContent = `Edit ${this.formatStepType(step.type)} Node`;
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'text-gray-500 hover:text-gray-700';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = () => document.body.removeChild(modal);
        
        header.appendChild(title);
        header.appendChild(closeBtn);
        modalContent.appendChild(header);
        
        // Form fields based on step type
        const form = document.createElement('form');
        form.className = 'space-y-4';
        
        // Name field (common to all step types)
        const nameGroup = document.createElement('div');
        const nameLabel = document.createElement('label');
        nameLabel.className = 'block text-sm font-medium text-gray-700 mb-1';
        nameLabel.textContent = 'Name';
        
        const nameInput = document.createElement('input');
        nameInput.className = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500';
        nameInput.value = step.name || '';
        
        nameGroup.appendChild(nameLabel);
        nameGroup.appendChild(nameInput);
        form.appendChild(nameGroup);
        
        // Step-specific fields
        if (step.type === 'message') {
            const textGroup = document.createElement('div');
            const textLabel = document.createElement('label');
            textLabel.className = 'block text-sm font-medium text-gray-700 mb-1';
            textLabel.textContent = 'Message Text';
            
            const textArea = document.createElement('textarea');
            textArea.className = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500';
            textArea.rows = 4;
            textArea.value = step.text || '';
            
            textGroup.appendChild(textLabel);
            textGroup.appendChild(textArea);
            form.appendChild(textGroup);
            
            // Next step selector
            if (step.id !== 'end') {
                const nextGroup = document.createElement('div');
                const nextLabel = document.createElement('label');
                nextLabel.className = 'block text-sm font-medium text-gray-700 mb-1';
                nextLabel.textContent = 'Next Step';
                
                const nextSelect = document.createElement('select');
                nextSelect.className = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500';
                
                // Add options for all steps except this one
                this.flowData.steps.forEach(s => {
                    if (s.id !== step.id) {
                        const option = document.createElement('option');
                        option.value = s.id;
                        option.textContent = s.name || s.id;
                        option.selected = step.next === s.id;
                        nextSelect.appendChild(option);
                    }
                });
                
                nextGroup.appendChild(nextLabel);
                nextGroup.appendChild(nextSelect);
                form.appendChild(nextGroup);
            }
        } else if (step.type === 'response') {
            // Branch editors
            const branchesGroup = document.createElement('div');
            const branchesLabel = document.createElement('label');
            branchesLabel.className = 'block text-sm font-medium text-gray-700 mb-1';
            branchesLabel.textContent = 'Response Branches';
            
            branchesGroup.appendChild(branchesLabel);
            
            // Create editors for each sentiment
            ['positive', 'neutral', 'negative'].forEach(sentiment => {
                const branchRow = document.createElement('div');
                branchRow.className = 'flex items-center space-x-2 mb-2';
                
                const sentimentLabel = document.createElement('span');
                sentimentLabel.className = 'text-sm font-medium w-24';
                sentimentLabel.textContent = this.formatSentiment(sentiment);
                
                const branchSelect = document.createElement('select');
                branchSelect.className = 'flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500';
                branchSelect.dataset.sentiment = sentiment;
                
                // Add options for all steps except this one
                this.flowData.steps.forEach(s => {
                    if (s.id !== step.id && s.type !== 'response') {
                        const option = document.createElement('option');
                        option.value = s.id;
                        option.textContent = s.name || s.id;
                        option.selected = step.branches && step.branches[sentiment] === s.id;
                        branchSelect.appendChild(option);
                    }
                });
                
                branchRow.appendChild(sentimentLabel);
                branchRow.appendChild(branchSelect);
                branchesGroup.appendChild(branchRow);
            });
            
            form.appendChild(branchesGroup);
        }
        
        // Form actions
        const actions = document.createElement('div');
        actions.className = 'flex justify-end space-x-2 pt-4 border-t';
        
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50';
        cancelBtn.textContent = 'Cancel';
        cancelBtn.type = 'button';
        cancelBtn.onclick = () => document.body.removeChild(modal);
        
        const saveBtn = document.createElement('button');
        saveBtn.className = 'px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700';
        saveBtn.textContent = 'Save Changes';
        saveBtn.type = 'button';
        saveBtn.onclick = () => {
            // Update the step with form values
            step.name = nameInput.value;
            
            if (step.type === 'message') {
                step.text = form.querySelector('textarea').value;
                if (step.id !== 'end') {
                    step.next = form.querySelector('select').value;
                }
            } else if (step.type === 'response') {
                if (!step.branches) step.branches = {};
                
                form.querySelectorAll('select[data-sentiment]').forEach(select => {
                    const sentiment = select.dataset.sentiment;
                    step.branches[sentiment] = select.value;
                });
            }
            
            // Update the flow and close the modal
            this.renderFlow();
            document.body.removeChild(modal);
        };
        
        actions.appendChild(cancelBtn);
        actions.appendChild(saveBtn);
        form.appendChild(actions);
        
        modalContent.appendChild(form);
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
    }

    deleteNode(stepId) {
        // Confirm deletion
        if (!confirm(`Are you sure you want to delete this step?`)) return;
        
        // Find the step to delete
        const stepIndex = this.flowData.steps.findIndex(s => s.id === stepId);
        if (stepIndex === -1) return;
        
        // Remove the step
        this.flowData.steps.splice(stepIndex, 1);
        
        // Update any references to this step
        this.flowData.steps.forEach(step => {
            if (step.next === stepId) {
                step.next = 'end';
            }
            
            if (step.branches) {
                Object.entries(step.branches).forEach(([sentiment, nextId]) => {
                    if (nextId === stepId) {
                        step.branches[sentiment] = 'end';
                    }
                });
            }
        });
        
        // Re-render the flow
        this.renderFlow();
    }

    addNewStep() {
        const stepId = `step_${Date.now()}`;
        const newStep = {
            id: stepId,
            type: 'message',
            name: 'New Step',
            text: 'Enter your message here...',
            next: 'end'
        };
        
        this.flowData.steps.push(newStep);
        this.renderFlow();
        this.editNode(newStep);
    }

    addNewResponseStep() {
        const stepId = `response_${Date.now()}`;
        const newStep = {
            id: stepId,
            type: 'response',
            name: 'New Response',
            branches: {
                positive: 'end',
                neutral: 'end',
                negative: 'end'
            }
        };
        
        this.flowData.steps.push(newStep);
        this.renderFlow();
        this.editNode(newStep);
    }

    setupEventListeners() {
        // Save button
        if (this.saveButton) {
            this.saveButton.addEventListener('click', () => this.saveFlow());
        }
        
        // Add buttons for new steps
        const addMessageBtn = document.getElementById('add-message-step');
        if (addMessageBtn) {
            addMessageBtn.addEventListener('click', () => this.addNewStep());
        }
        
        const addResponseBtn = document.getElementById('add-response-step');
        if (addResponseBtn) {
            addResponseBtn.addEventListener('click', () => this.addNewResponseStep());
        }
    }

    saveFlow() {
        // Validate the flow
        if (!this.validateFlow()) {
            alert('The flow contains errors. Please check that all steps are properly connected.');
            return;
        }
        
        // Get the form element
        const form = document.getElementById('flow-form');
        if (!form) return;
        
        // Create a hidden input with the flow data
        let flowDataInput = document.getElementById('flow-data-input');
        if (!flowDataInput) {
            flowDataInput = document.createElement('input');
            flowDataInput.type = 'hidden';
            flowDataInput.name = 'flow_data';
            flowDataInput.id = 'flow-data-input';
            form.appendChild(flowDataInput);
        }
        
        // Set the value and submit the form
        flowDataInput.value = JSON.stringify(this.flowData);
        form.submit();
    }

    validateFlow() {
        // Check if intro exists
        const hasIntro = this.flowData.steps.some(s => s.id === 'intro');
        if (!hasIntro) return false;
        
        // Check if end exists
        const hasEnd = this.flowData.steps.some(s => s.id === 'end');
        if (!hasEnd) return false;
        
        // Check that all message steps have a next step
        const messageStepsValid = this.flowData.steps
            .filter(s => s.type === 'message' && s.id !== 'end')
            .every(s => s.next && this.flowData.steps.some(step => step.id === s.next));
        
        if (!messageStepsValid) return false;
        
        // Check that all response steps have valid branches
        const responseStepsValid = this.flowData.steps
            .filter(s => s.type === 'response')
            .every(s => s.branches && 
                Object.values(s.branches).every(nextId => 
                    this.flowData.steps.some(step => step.id === nextId)
                )
            );
        
        return responseStepsValid;
    }

    formatStepType(type) {
        switch (type) {
            case 'message': return 'Message';
            case 'response': return 'Response';
            case 'end': return 'End';
            default: return type;
        }
    }

    formatSentiment(sentiment) {
        switch (sentiment) {
            case 'positive': return 'Positive';
            case 'neutral': return 'Neutral';
            case 'negative': return 'Negative';
            default: return sentiment;
        }
    }

    // Load flow data from JSON
    loadFlow(flowData) {
        this.flowData = flowData;
        this.renderFlow();
    }

    // Get the current flow data
    getFlowData() {
        return this.flowData;
    }
}

// Initialize the flow builder when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the flow builder page
    const flowContainer = document.getElementById('flow-container');
    const saveButton = document.getElementById('save-flow');
    
    if (flowContainer && saveButton) {
        // Get the initial flow data if available
        let flowData = null;
        const flowDataElement = document.getElementById('initial-flow-data');
        
        if (flowDataElement) {
            try {
                flowData = JSON.parse(flowDataElement.textContent);
            } catch (e) {
                console.error('Error parsing flow data:', e);
            }
        }
        
        // Initialize the flow builder
        window.flowBuilder = new FlowBuilder('flow-container', 'save-flow', flowData);
    }
});
