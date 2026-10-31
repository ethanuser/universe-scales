// Universal Scales - Item Editor Module
// Handles visual editing of items, image uploads, and YAML import/export

class ItemEditor {
    constructor(app) {
        this.app = app; // Reference to main UniversalScales instance

        // DOM elements
        this.editorToggle = document.getElementById('editor-toggle');
        this.editorContent = document.getElementById('editor-content');
        this.itemsList = document.getElementById('items-list');
        this.addItemBtn = document.getElementById('add-item-btn');
        this.deleteAllItemsBtn = document.getElementById('delete-all-items-btn');
        this.importYamlBtn = document.getElementById('import-yaml-btn');
        this.exportYamlBtn = document.getElementById('export-yaml-btn');
        this.dimensionNameInput = document.getElementById('dimension-name-input');
        this.dimensionDescriptionInput = document.getElementById('dimension-description-input');
        this.unitsList = document.getElementById('units-list');
        this.addUnitBtn = document.getElementById('add-unit-btn');
        this.deleteAllUnitsBtn = document.getElementById('delete-all-units-btn');
        this.clearDimensionInfoBtn = document.getElementById('clear-dimension-info-btn');
        this.sharePlotBtn = document.getElementById('share-plot-btn');

        // Store dimension and unit overrides
        this.dimensionOverrides = {};
        this.unitOverrides = {};

        // Store section collapsed states
        this.sectionStates = {};

        this.setupEventListeners();
        this.loadCustomItems();
        this.loadSectionStates();
        this.applySectionStates();
    }

    setupEventListeners() {
        this.editorToggle.addEventListener('click', () => {
            this.toggleEditor();
        });

        this.addItemBtn.addEventListener('click', () => {
            this.addNewItem();
        });

        this.deleteAllItemsBtn.addEventListener('click', () => {
            this.deleteAllItems(true);
        });

        this.addUnitBtn.addEventListener('click', () => {
            this.addNewUnit();
        });

        this.deleteAllUnitsBtn.addEventListener('click', () => {
            this.deleteAllUnits(true);
        });

        this.clearDimensionInfoBtn.addEventListener('click', () => {
            this.clearDimensionInfo();
        });

        this.importYamlBtn.addEventListener('click', () => {
            this.showYamlImportModal();
        });

        this.exportYamlBtn.addEventListener('click', () => {
            this.exportToYaml();
        });

        if (this.sharePlotBtn) {
            this.sharePlotBtn.addEventListener('click', () => {
                this.generateShareLink();
            });
        }

        // Setup save button
        this.setupSaveButton();
        // Setup undo button
        this.setupUndoButton();
    }

    setupSaveButton() {
        // Check if button already exists
        let saveButton = document.getElementById('editor-save-all-btn');

        if (!saveButton) {
            // Create save button and add it to the header
            saveButton = document.createElement('button');
            saveButton.id = 'editor-save-all-btn';
            saveButton.className = 'btn btn-primary';
            saveButton.textContent = 'Save all changes';
            saveButton.onclick = () => this.saveAllItems();

            // Add to editor-actions div
            const editorActions = document.querySelector('.editor-actions');
            if (editorActions) {
                editorActions.appendChild(saveButton);
            }
        }
    }

    setupUndoButton() {
        // Check if button already exists
        let undoButton = document.getElementById('editor-undo-all-btn');

        if (!undoButton) {
            // Create undo button and add it to the header
            undoButton = document.createElement('button');
            undoButton.id = 'editor-undo-all-btn';
            undoButton.className = 'btn btn-secondary';
            undoButton.textContent = 'Undo all changes';
            undoButton.onclick = () => this.undoAllChanges();

            // Add to editor-actions div (before save button)
            const editorActions = document.querySelector('.editor-actions');
            if (editorActions) {
                const saveButton = document.getElementById('editor-save-all-btn');
                if (saveButton) {
                    editorActions.insertBefore(undoButton, saveButton);
                } else {
                    editorActions.appendChild(undoButton);
                }
            }
        }
    }

    deleteAllItems(showConfirmation = true) {
        if (showConfirmation) {
            if (!confirm('Are you sure you want to delete ALL items? This will remove all original and custom items for this dimension.')) {
                return;
            }
        }

        // Initialize custom items array if needed
        if (!this.app.customItems[this.app.currentDimension]) {
            this.app.customItems[this.app.currentDimension] = [];
        }

        // Get all original items
        const originalItems = this.app.dimensionData?.items || [];

        // Mark all original items as deleted
        originalItems.forEach((item, index) => {
            // Check if there's already a marker for this item
            const existingMarker = this.app.customItems[this.app.currentDimension].find(
                custom => custom.originalIndex === index
            );

            if (existingMarker) {
                // Update existing marker to mark as deleted
                existingMarker.isDeleted = true;
                existingMarker.isOverride = false;
            } else {
                // Create a new deletion marker
                this.app.customItems[this.app.currentDimension].push({
                    originalIndex: index,
                    isCustom: false,
                    isOverride: false,
                    isDeleted: true
                });
            }
        });

        // Remove all standalone custom items (items with isCustom: true and no originalIndex)
        this.app.customItems[this.app.currentDimension] = this.app.customItems[this.app.currentDimension].filter(
            item => item.originalIndex !== undefined
        );

        // Save to localStorage
        this.saveCustomItems();

        // Refresh the editor display
        this.renderEditorItems();

        // Update the plot
        this.app.plot.updatePlot();

        if (showConfirmation) {
            AppFeedback.toast('All items have been deleted!', 'success');
        }
    }

    undoAllChanges() {
        if (!confirm('Are you sure you want to undo all changes? This will remove all custom items, edits, deletions, and metadata changes for this dimension.')) {
            return;
        }

        // Clear all custom items for the current dimension
        if (this.app.customItems[this.app.currentDimension]) {
            this.app.customItems[this.app.currentDimension] = [];
        }

        // Clear dimension and unit overrides for the current dimension
        if (this.dimensionOverrides[this.app.currentDimension]) {
            delete this.dimensionOverrides[this.app.currentDimension];
        }
        if (this.unitOverrides[this.app.currentDimension]) {
            delete this.unitOverrides[this.app.currentDimension];
        }

        // Save to localStorage
        this.saveCustomItems();

        // Refresh the editor display
        this.renderDimensionMetadata();
        this.renderUnits();
        this.renderEditorItems();

        // Update the plot
        this.app.plot.updatePlot();
        document.dispatchEvent(new CustomEvent('editor-reset'));
    }

    toggleEditor() {
        const isExpanded = this.editorContent.style.display !== 'none';
        this.editorContent.style.display = isExpanded ? 'none' : 'block';
        this.editorToggle.classList.toggle('expanded', !isExpanded);

        if (!isExpanded) {
            this.renderDimensionMetadata();
            this.renderUnits();
            this.renderEditorItems();
            this.applySectionStates();
        }
    }

    toggleSection(sectionId) {
        const section = document.getElementById(`${sectionId}-section`);
        if (!section) return;

        const isCollapsed = section.classList.contains('collapsed');
        const newState = !isCollapsed; // Toggle: if collapsed, expand; if expanded, collapse

        this.sectionStates[sectionId] = newState;
        section.classList.toggle('collapsed', newState);
        this.saveSectionStates();
    }

    loadSectionStates() {
        const saved = localStorage.getItem('editorSectionStates');
        if (saved) {
            try {
                this.sectionStates = JSON.parse(saved);
            } catch (e) {
                console.error('Error loading section states:', e);
                this.sectionStates = {};
            }
        } else {
            // Default: all sections expanded
            this.sectionStates = {
                'dimension-metadata': false,
                'units': false,
                'items': false
            };
        }
    }

    saveSectionStates() {
        try {
            localStorage.setItem('editorSectionStates', JSON.stringify(this.sectionStates));
        } catch (e) {
            console.error('Error saving section states:', e);
        }
    }

    applySectionStates() {
        Object.keys(this.sectionStates).forEach(sectionId => {
            const section = document.getElementById(`${sectionId}-section`);
            if (section) {
                section.classList.toggle('collapsed', this.sectionStates[sectionId]);
            }
        });
    }

    renderDimensionMetadata() {
        if (!this.app.dimensionData) return;

        // Get dimension name (from currentDimension or override)
        const dimensionName = this.dimensionOverrides[this.app.currentDimension]?.name ||
            this.app.currentDimension;
        const dimensionDescription = this.dimensionOverrides[this.app.currentDimension]?.description ||
            this.app.dimensionData.dimension_description || '';

        if (this.dimensionNameInput) {
            this.dimensionNameInput.value = dimensionName;
        }
        if (this.dimensionDescriptionInput) {
            this.dimensionDescriptionInput.value = dimensionDescription;
        }

        // Update header to reflect dimension name
        this.updateEditorHeader();
    }

    renderUnits() {
        if (!this.app.dimensionData || !this.unitsList) return;

        // Clear the list completely
        this.unitsList.innerHTML = '';

        // Get the current units array (which may have been reordered)
        const units = this.app.dimensionData.units || [];
        const overrides = this.unitOverrides[this.app.currentDimension] || {};

        // Calculate display index based on visible units only
        let displayIndex = 1;

        units.forEach((unit, arrayIndex) => {
            // Check if unit is deleted using the current array index
            const isDeleted = overrides[arrayIndex]?.isDeleted === true;

            // Skip if unit is undefined or deleted
            if (!unit || isDeleted) {
                return;
            }

            // Create card with current array index and sequential display index
            const unitCard = this.createUnitEditorCard(unit, arrayIndex, displayIndex);
            this.unitsList.appendChild(unitCard);
            displayIndex++; // Increment only for visible units
        });

        // Update header to reflect unit count
        this.updateEditorHeader();
    }

    updateEditorHeader() {
        const editorHeader = document.querySelector('.editor-header h3');
        if (!editorHeader || !this.app.dimensionData) return;

        // Get dimension name (from override or current dimension)
        const dimensionName = this.dimensionOverrides[this.app.currentDimension]?.name ||
            this.app.currentDimension;
        // Capitalize only first letter
        const dimensionNameCapitalized = dimensionName.charAt(0).toUpperCase() + dimensionName.slice(1).toLowerCase();

        editorHeader.textContent = dimensionNameCapitalized;

        // Update section headers with counts
        this.updateSectionHeaders();

        // Update dimension dropdown
        this.updateDimensionSelector();
    }

    updateDimensionSelector() {
        if (!this.app.dimensionSelect) return;

        // Find the option for the current dimension
        const option = this.app.dimensionSelect.querySelector(`option[value="${this.app.currentDimension}"]`);
        if (!option) return;

        // Get dimension name (from override or use default)
        const dimensionName = this.dimensionOverrides[this.app.currentDimension]?.name;

        if (dimensionName) {
            // Use the override name, capitalize first letter
            const dimensionNameCapitalized = dimensionName.charAt(0).toUpperCase() + dimensionName.slice(1).toLowerCase();
            option.textContent = dimensionNameCapitalized;
        } else {
            // Restore original name from HTML
            // Store original names if not already stored
            if (!this.originalDimensionNames) {
                this.originalDimensionNames = {};
                const allOptions = this.app.dimensionSelect.querySelectorAll('option');
                allOptions.forEach(opt => {
                    this.originalDimensionNames[opt.value] = opt.textContent;
                });
            }

            // Restore original name if available, otherwise use fallback
            const originalName = this.originalDimensionNames[this.app.currentDimension];
            if (originalName) {
                option.textContent = originalName;
            } else {
                // Fallback: capitalize dimension value
                const defaultName = this.app.currentDimension.charAt(0).toUpperCase() +
                    this.app.currentDimension.slice(1).replace(/-/g, ' ');
                option.textContent = defaultName;
            }
        }
    }

    updateSectionHeaders() {
        // Count units (excluding deleted ones)
        const units = this.app.dimensionData?.units || [];
        const unitCount = units.filter((unit, idx) =>
            !this.unitOverrides[this.app.currentDimension]?.[idx]?.isDeleted
        ).length;

        // Count items
        const allItems = this.getAllItemsForEditor();
        const itemCount = allItems.length;

        // Update Units section header
        const unitsHeader = document.querySelector('#units-section .section-header-left h4');
        if (unitsHeader) {
            unitsHeader.textContent = `Units (${unitCount})`;
        }

        // Update Items section header
        const itemsHeader = document.querySelector('#items-section .section-header-left h4');
        if (itemsHeader) {
            itemsHeader.textContent = `Items (${itemCount})`;
        }
    }

    createUnitEditorCard(unit, index, displayIndex) {
        const card = document.createElement('div');
        card.className = 'unit-editor-card';
        card.dataset.unitIndex = index;

        // Get override values if they exist
        const override = this.unitOverrides[this.app.currentDimension]?.[index];
        const unitName = override?.name !== undefined ? override.name : unit.name;
        const unitSymbol = override?.symbol !== undefined ? override.symbol : unit.symbol;
        const unitDescription = override?.description !== undefined ? override.description : (unit.description || '');

        // Capitalize first letter for display
        const unitNameCapitalized = unitName ? unitName.charAt(0).toUpperCase() + unitName.slice(1).toLowerCase() : 'Unnamed Unit';

        card.innerHTML = `
            <div class="unit-editor-card-header">
                <div class="unit-editor-card-title-row">
                    <h5>${displayIndex}. ${this.escapeHtml(unitNameCapitalized)}</h5>
                    <div class="unit-drag-handle" title="Drag to reorder">
                        <span class="drag-handle-icon">☰</span>
                    </div>
                    <button class="btn btn-small btn-danger" onclick="window.app.editor.deleteUnit(${index})">Delete unit</button>
                </div>
            </div>
            <div class="unit-editor-form">
                <div class="unit-name-symbol-row">
                    <div class="editor-form-group unit-name-group">
                        <label>Name *</label>
                        <input type="text" name="unit-name" value="${this.escapeHtml(unitName)}" required>
                    </div>
                    <div class="editor-form-group unit-symbol-group">
                        <label>Symbol *</label>
                        <input type="text" name="unit-symbol" value="${this.escapeHtml(unitSymbol)}" required>
                    </div>
                </div>
                <div class="editor-form-group">
                    <label>Description</label>
                    <textarea name="unit-description">${this.escapeHtml(unitDescription)}</textarea>
                </div>
            </div>
        `;

        // Add drag event listeners to the card for drop zones
        card.addEventListener('dragover', (e) => this.handleUnitDragOver(e));
        card.addEventListener('drop', (e) => this.handleUnitDrop(e, index));

        // Make only the drag handle draggable
        const dragHandle = card.querySelector('.unit-drag-handle');
        if (dragHandle) {
            dragHandle.draggable = true;
            dragHandle.addEventListener('dragstart', (e) => {
                e.stopPropagation();
                this.handleUnitDragStart(e, index);
            });
            dragHandle.addEventListener('dragend', (e) => {
                e.stopPropagation();
                this.handleUnitDragEnd(e);
            });
        }

        // Prevent dragging on inputs/textareas/buttons
        const inputs = card.querySelectorAll('input, textarea, button');
        inputs.forEach(input => {
            input.draggable = false;
        });

        return card;
    }

    handleUnitDragStart(e, index) {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', index.toString());
        // Add dragging class to the parent card
        const card = e.currentTarget.closest('.unit-editor-card');
        if (card) {
            card.classList.add('dragging');
        }
    }

    handleUnitDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        const draggingCard = document.querySelector('.unit-editor-card.dragging');
        if (!draggingCard) return;

        const cards = Array.from(document.querySelectorAll('.unit-editor-card:not(.dragging)'));
        const afterElement = cards.reduce((closest, card) => {
            const box = card.getBoundingClientRect();
            const offset = e.clientY - box.top - box.height / 2;

            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: card };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;

        const unitsList = document.getElementById('units-list');
        if (afterElement == null) {
            unitsList.appendChild(draggingCard);
        } else {
            unitsList.insertBefore(draggingCard, afterElement);
        }
    }

    handleUnitDrop(e, dropIndex) {
        e.preventDefault();
        e.stopPropagation();

        const draggedIndex = parseInt(e.dataTransfer.getData('text/plain'));

        // Get the dragged card (it's still in the DOM with the dragging class)
        const draggedCard = document.querySelector('.unit-editor-card.dragging');
        if (!draggedCard) return;

        // Use setTimeout to ensure DOM has fully updated after handleUnitDragOver
        setTimeout(() => {
            // Get the final DOM order - include ALL cards in their current visual order
            // The dragged card is already in its new position due to handleUnitDragOver
            const unitsList = document.getElementById('units-list');
            if (!unitsList) return;

            const allCards = Array.from(unitsList.querySelectorAll('.unit-editor-card'));
            const finalOrder = allCards.map(card => parseInt(card.dataset.unitIndex));

            // Get current state
            const units = [...this.app.dimensionData.units];
            const oldOverrides = this.unitOverrides[this.app.currentDimension] || {};

            // Separate visible and deleted units with their original indices
            const visibleUnits = [];
            const deletedUnits = [];

            units.forEach((unit, idx) => {
                const isDeleted = oldOverrides[idx]?.isDeleted;
                if (isDeleted) {
                    deletedUnits.push({ unit, originalIndex: idx });
                } else {
                    visibleUnits.push({ unit, originalIndex: idx });
                }
            });

            // Reorder visible units based on the final DOM order
            // finalOrder contains the old indices in their new visual order
            const reorderedVisibleUnits = [];
            const reorderedVisibleIndices = [];

            finalOrder.forEach(oldIndex => {
                const found = visibleUnits.find(v => v.originalIndex === oldIndex);
                if (found) {
                    reorderedVisibleUnits.push(found.unit);
                    reorderedVisibleIndices.push(found.originalIndex);
                }
            });

            // Make sure we didn't lose any units
            if (reorderedVisibleUnits.length !== visibleUnits.length) {
                console.error('Unit reordering error: lost some units during reorder', {
                    expected: visibleUnits.length,
                    got: reorderedVisibleUnits.length,
                    finalOrder,
                    visibleUnits: visibleUnits.map(v => v.originalIndex)
                });
                return;
            }

            // Combine reordered visible units with deleted units
            // reorderedVisibleUnits is already an array of unit objects, not {unit, originalIndex}
            const reorderedUnits = [...reorderedVisibleUnits, ...deletedUnits.map(d => d.unit)];

            // Remap overrides: old index -> new index
            const newOverrides = {};

            // Map visible units' overrides to their new positions
            reorderedVisibleIndices.forEach((oldIndex, newIndex) => {
                if (oldOverrides[oldIndex]) {
                    newOverrides[newIndex] = { ...oldOverrides[oldIndex] };
                    // Ensure isDeleted is false for visible units
                    newOverrides[newIndex].isDeleted = false;
                }
            });

            // Map deleted units' overrides to their positions (after visible units)
            deletedUnits.forEach((deleted, deletedIndex) => {
                const newIndex = reorderedVisibleUnits.length + deletedIndex;
                if (oldOverrides[deleted.originalIndex]) {
                    newOverrides[newIndex] = { ...oldOverrides[deleted.originalIndex] };
                    // Ensure isDeleted is true for deleted units
                    newOverrides[newIndex].isDeleted = true;
                } else {
                    // Create deletion marker if it doesn't exist
                    newOverrides[newIndex] = { isDeleted: true };
                }
            });

            // Update the units array and overrides
            this.app.dimensionData.units = reorderedUnits;
            this.unitOverrides[this.app.currentDimension] = newOverrides;

            this.saveCustomItems();

            // Force a complete re-render - this will update numbering and recreate all cards
            this.renderUnits();
            this.app.updateUnitSelector();
            this.app.plot.updatePlot();
        }, 0);
    }

    handleUnitDragEnd(e) {
        // Remove dragging class from the parent card
        const card = e.currentTarget.closest('.unit-editor-card');
        if (card) {
            card.classList.remove('dragging');
        }
    }

    deleteUnit(index) {
        // Mark unit as deleted in overrides
        if (!this.unitOverrides[this.app.currentDimension]) {
            this.unitOverrides[this.app.currentDimension] = {};
        }
        if (!this.unitOverrides[this.app.currentDimension][index]) {
            this.unitOverrides[this.app.currentDimension][index] = {};
        }
        this.unitOverrides[this.app.currentDimension][index].isDeleted = true;

        this.saveCustomItems();
        this.renderUnits();
        // Note: We'd need to update the unit selector in script.js, but for now just re-render
        this.app.updateUnitSelector();
        // Header is updated in renderUnits
    }

    addNewUnit() {
        if (!this.app.dimensionData) return;

        // Initialize units array if it doesn't exist
        if (!this.app.dimensionData.units) {
            this.app.dimensionData.units = [];
        }

        // Create new unit with default values
        const newUnit = {
            name: '',
            symbol: '',
            description: '',
            conversion_factor: 1
        };

        // Add to units array at position 1 (beginning)
        this.app.dimensionData.units.unshift(newUnit);

        // Re-render units
        this.renderUnits();
        this.app.updateUnitSelector();
    }

    deleteAllUnits(showConfirmation = true) {
        if (showConfirmation) {
            if (!confirm('Are you sure you want to delete ALL units? This will remove all units for this dimension.')) {
                return;
            }
        }

        if (!this.app.dimensionData || !this.app.dimensionData.units) return;

        // Initialize unit overrides if needed
        if (!this.unitOverrides[this.app.currentDimension]) {
            this.unitOverrides[this.app.currentDimension] = {};
        }

        // Mark all units as deleted
        this.app.dimensionData.units.forEach((unit, index) => {
            if (!this.unitOverrides[this.app.currentDimension][index]) {
                this.unitOverrides[this.app.currentDimension][index] = {};
            }
            this.unitOverrides[this.app.currentDimension][index].isDeleted = true;
        });

        this.saveCustomItems();
        this.renderUnits();
        this.app.updateUnitSelector();

        if (showConfirmation) {
            AppFeedback.toast('All units have been deleted!', 'success');
        }
    }

    clearDimensionInfo() {
        if (!confirm('Are you sure you want to clear the dimension name and description?')) {
            return;
        }

        // Clear the input fields
        if (this.dimensionNameInput) {
            this.dimensionNameInput.value = '';
        }
        if (this.dimensionDescriptionInput) {
            this.dimensionDescriptionInput.value = '';
        }

        // Remove dimension overrides
        if (this.dimensionOverrides[this.app.currentDimension]) {
            delete this.dimensionOverrides[this.app.currentDimension].name;
            delete this.dimensionOverrides[this.app.currentDimension].description;

            // If the override object is now empty, remove it
            if (Object.keys(this.dimensionOverrides[this.app.currentDimension]).length === 0) {
                delete this.dimensionOverrides[this.app.currentDimension];
            }
        }

        this.saveCustomItems();
        this.renderDimensionMetadata();
    }

    renderEditorItems() {
        if (!this.app.dimensionData) return;

        this.itemsList.innerHTML = '';

        // Get all items (original + custom)
        const allItems = this.getAllItemsForEditor();

        // Sort items by value (smallest to largest) to match the plot order
        const sortedItems = [...allItems].sort((a, b) => {
            const valueA = parseFloat(a.value) || 0;
            const valueB = parseFloat(b.value) || 0;
            return valueA - valueB;
        });

        // Update header to reflect counts
        this.updateEditorHeader();

        sortedItems.forEach((item, index) => {
            const card = this.createItemEditorCard(item, index + 1); // Use 1-based numbering
            this.itemsList.appendChild(card);
        });
    }

    getAllItemsForEditor() {
        const originalItems = this.app.dimensionData.items || [];
        const customItems = this.app.customItems[this.app.currentDimension] || [];

        // Merge original and custom items, applying overrides and excluding deleted items
        const allItems = [];

        originalItems.forEach((item, index) => {
            // Check if this item is deleted
            const isDeleted = customItems.some(
                custom => custom.originalIndex === index && custom.isDeleted
            );

            if (!isDeleted) {
                // Check if there's an override
                const override = customItems.find(
                    custom => custom.originalIndex === index && custom.isOverride && !custom.isDeleted
                );

                if (override) {
                    // Merge override with original
                    allItems.push({
                        ...item,
                        ...override,
                        isCustom: false,
                        originalIndex: index
                    });
                } else {
                    allItems.push({
                        ...item,
                        isCustom: false,
                        originalIndex: index
                    });
                }
            }
        });

        // Add custom items (not overrides, not deleted)
        customItems.forEach(customItem => {
            if (customItem.isCustom && !customItem.isOverride && !customItem.isDeleted) {
                // Ensure customId exists
                if (!customItem.customId) {
                    customItem.customId = `custom-${Date.now()}-${Math.random()}`;
                }
                allItems.push({
                    ...customItem,
                    isCustom: true,
                    customId: customItem.customId
                });
            }
        });

        return allItems;
    }

    getCurrentImagePath(item) {
        // Check if imageData is explicitly null (image was removed)
        // This handles the case where an override has imageData: null
        if (item.imageData === null) {
            return null;
        }

        // Also check if there's an override that explicitly removed the image
        // This is a safety check in case the merge didn't work as expected
        if (item.originalIndex !== undefined) {
            const customItems = this.app.customItems[this.app.currentDimension] || [];
            const override = customItems.find(
                custom => custom.originalIndex === item.originalIndex &&
                    custom.isOverride &&
                    !custom.isDeleted &&
                    custom.imageData === null
            );
            if (override) {
                return null;
            }
        }

        // First check if there's imageData (custom uploaded image)
        if (item.imageData) {
            return item.imageData;
        }

        // Otherwise use the same logic as getImagePath in script.js
        const sanitizedDimension = this.app.currentDimension
            .replace(/[^\w\s-]/g, '')  // Remove special characters
            .replace(/[-\s]+/g, '_')    // Replace spaces and dashes with underscores
            .toLowerCase();

        const sanitizedName = (item.name || '')
            .replace(/[^\w\s-]/g, '')  // Remove special characters
            .replace(/[-\s]+/g, '_')    // Replace spaces and dashes with underscores
            .toLowerCase();

        const baseFilename = `${sanitizedDimension}_${sanitizedName}`;
        return `images/${baseFilename}`;
    }

    createItemEditorCard(item, itemNumber) {
        const card = document.createElement('div');
        card.className = 'item-editor-card';
        // Store originalIndex for original items (needed for overrides), or use itemNumber for display
        if (item.originalIndex !== undefined) {
            card.dataset.itemIndex = item.originalIndex;
        } else {
            card.dataset.itemIndex = itemNumber - 1; // Fallback for custom items without originalIndex
        }
        card.dataset.isCustom = item.isCustom ? 'true' : 'false';
        // Always set customId for custom items, generate one if missing
        if (item.isCustom) {
            card.dataset.customId = item.customId || `custom-${Date.now()}-${Math.random()}`;
        } else if (item.customId) {
            card.dataset.customId = item.customId;
        }

        // Get current image path (either imageData or file path)
        const currentImagePath = this.getCurrentImagePath(item);
        const hasImageData = !!item.imageData;

        // Build image preview with smart fallback and caching
        let imagePreview = '';
        if (currentImagePath) {
            let imagePreviewSrc = currentImagePath;
            let thumbPath = '';

            if (!currentImagePath.startsWith('data:image')) {
                const basePath = currentImagePath.replace(/\.(jpg|jpeg|png)$/i, '');
                thumbPath = basePath.replace('images/', 'images/thumbs/') + '.jpg';

                // If we know the thumbnail fails, skip it
                if (window.app.failedUrls?.has(thumbPath)) {
                    imagePreviewSrc = currentImagePath;
                } else {
                    imagePreviewSrc = thumbPath;
                }
            }

            // Check if we know both versions fail
            const isFullFailed = window.app.failedUrls?.has(currentImagePath);
            const isThumbFailed = thumbPath && window.app.failedUrls?.has(thumbPath);

            // If the only option we have is already failed, don't even create the img tag
            if (!(isFullFailed && (imagePreviewSrc === currentImagePath || isThumbFailed))) {
                const onerror = `window.app.recordImageFailure(this.src); if(this.src!=='${currentImagePath}'){ if(!window.app.failedUrls?.has('${currentImagePath}')){ this.src='${currentImagePath}' } else { this.style.display='none' } }else{this.style.display='none'}`;
                imagePreview = `<img src="${imagePreviewSrc}" alt="Preview" class="image-preview" onerror="${onerror}">`;
            }
        }

        const header = document.createElement('div');
        header.className = 'item-editor-card-header';
        header.innerHTML = `
            <div class="item-editor-card-title-row">
                <h4>${itemNumber}. ${item.name || 'Unnamed Item'}</h4>
                <button class="btn btn-small btn-danger" onclick="window.app.editor.deleteItem(event)">Delete item</button>
            </div>
        `;

        const form = document.createElement('form');
        form.className = 'item-editor-form';
        form.innerHTML = `
            <div class="item-editor-form-left">
                <div class="item-editor-form-group">
                    <label>Name *</label>
                    <input type="text" name="name" value="${this.escapeHtml(item.name || '')}" required>
                </div>
                <div class="item-editor-form-group">
                    <label>Value *</label>
                    <input type="number" name="value" step="any" value="${item.value || ''}" required>
                </div>
                <div class="item-editor-form-group">
                    <label>Description</label>
                    <textarea name="description">${this.escapeHtml(item.description || '')}</textarea>
                </div>
                <div class="item-editor-form-group">
                    <label>Source URL</label>
                    <input type="url" name="source" value="${this.escapeHtml(item.source || '')}">
                </div>
            </div>
            <div class="item-editor-form-right image-upload-section">
                <div class="image-upload-controls">
                    <div class="file-input-wrapper">
                        <input type="file" accept="image/*" onchange="window.app.editor.handleImageUpload(event, ${itemNumber})" id="file-${itemNumber}">
                        <label for="file-${itemNumber}" class="btn btn-small">Choose Image</label>
                    </div>
                    ${currentImagePath ? '<button type="button" class="btn btn-small btn-danger" onclick="window.app.editor.removeImage(event, ' + itemNumber + ')">Delete Image</button>' : ''}
                </div>
                <div class="image-preview-container">
                    ${imagePreview}
                </div>
            </div>
        `;

        card.appendChild(header);
        card.appendChild(form);

        // After card is added to DOM, set up image preview click handler
        setTimeout(() => {
            const imagePreview = card.querySelector('.image-preview');
            if (imagePreview && currentImagePath && !currentImagePath.startsWith('data:image')) {
                // Check if this is a thumbnail by checking if src contains 'thumbs'
                const isThumbnail = imagePreview.src.includes('/thumbs/');
                if (isThumbnail) {
                    imagePreview.classList.add('thumbnail-image');
                    imagePreview.style.cursor = 'zoom-in';
                    imagePreview.title = 'Click to view full resolution';

                    imagePreview.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        if (imagePreview.dataset.loading === 'true') {
                            return;
                        }

                        // Get full-resolution image path
                        let basePath = currentImagePath;
                        if (basePath && !basePath.startsWith('data:image')) {
                            if (basePath.includes('.')) {
                                basePath = basePath.replace(/\.(jpg|jpeg|png)$/i, '');
                            }
                            // Open modal with full-resolution image
                            this.app.openImageModal(basePath, item.name || 'Image');
                        }
                    });
                }
            }
        }, 0);

        return card;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    addNewItem() {
        const newItem = {
            name: '',
            value: 0,
            description: '',
            source: '',
            isCustom: true,
            customId: `custom-${Date.now()}-${Math.random()}`
        };

        if (!this.app.customItems[this.app.currentDimension]) {
            this.app.customItems[this.app.currentDimension] = [];
        }

        this.app.customItems[this.app.currentDimension].push(newItem);
        this.saveCustomItems();
        this.renderEditorItems();
        this.app.plot.updatePlot();
    }

    saveAllItems() {
        // Save dimension metadata
        if (this.dimensionNameInput && this.dimensionDescriptionInput) {
            const dimensionName = this.dimensionNameInput.value.trim();
            const dimensionDescription = this.dimensionDescriptionInput.value.trim();

            if (!this.dimensionOverrides[this.app.currentDimension]) {
                this.dimensionOverrides[this.app.currentDimension] = {};
            }

            if (dimensionName && dimensionName !== this.app.currentDimension) {
                this.dimensionOverrides[this.app.currentDimension].name = dimensionName;
            } else {
                delete this.dimensionOverrides[this.app.currentDimension].name;
            }

            if (dimensionDescription && dimensionDescription !== (this.app.dimensionData?.dimension_description || '')) {
                this.dimensionOverrides[this.app.currentDimension].description = dimensionDescription;
            } else {
                delete this.dimensionOverrides[this.app.currentDimension].description;
            }

            // Update dimension selector dropdown after saving name
            this.updateDimensionSelector();
        }

        // Save unit metadata
        if (this.unitsList) {
            const unitCards = this.unitsList.querySelectorAll('.unit-editor-card');
            unitCards.forEach((card) => {
                const unitIndex = parseInt(card.dataset.unitIndex);
                const form = card.querySelector('.unit-editor-form');
                if (!form) return;

                // Read input values directly since it's a div, not a form element
                const nameInput = form.querySelector('input[name="unit-name"]');
                const symbolInput = form.querySelector('input[name="unit-symbol"]');
                const descriptionInput = form.querySelector('textarea[name="unit-description"]');

                const unitData = {
                    name: nameInput?.value?.trim() || '',
                    symbol: symbolInput?.value?.trim() || '',
                    description: descriptionInput?.value?.trim() || ''
                };

                // Validate
                if (!unitData.name || !unitData.symbol) {
                    return; // Skip invalid units
                }

                // Get original unit for comparison
                const originalUnit = this.app.dimensionData?.units?.[unitIndex];
                if (!originalUnit) return;

                // Initialize unit overrides if needed
                if (!this.unitOverrides[this.app.currentDimension]) {
                    this.unitOverrides[this.app.currentDimension] = {};
                }
                if (!this.unitOverrides[this.app.currentDimension][unitIndex]) {
                    this.unitOverrides[this.app.currentDimension][unitIndex] = {};
                }

                // Save only if changed
                if (unitData.name !== originalUnit.name) {
                    this.unitOverrides[this.app.currentDimension][unitIndex].name = unitData.name;
                } else {
                    delete this.unitOverrides[this.app.currentDimension][unitIndex].name;
                }

                if (unitData.symbol !== originalUnit.symbol) {
                    this.unitOverrides[this.app.currentDimension][unitIndex].symbol = unitData.symbol;
                } else {
                    delete this.unitOverrides[this.app.currentDimension][unitIndex].symbol;
                }

                if (unitData.description !== (originalUnit.description || '')) {
                    this.unitOverrides[this.app.currentDimension][unitIndex].description = unitData.description;
                } else {
                    delete this.unitOverrides[this.app.currentDimension][unitIndex].description;
                }
            });
        }

        // Collect all item data from all cards
        const allCards = this.itemsList.querySelectorAll('.item-editor-card');
        const itemsToSave = [];
        const errors = [];
        const invalidCards = [];

        allCards.forEach((card, index) => {
            const form = card.querySelector('.item-editor-form');
            if (!form) return;

            const formData = new FormData(form);
            const itemData = {
                name: formData.get('name'),
                value: parseFloat(formData.get('value')),
                description: formData.get('description') || '',
                source: formData.get('source') || ''
            };

            // Validate
            if (!itemData.name || isNaN(itemData.value)) {
                errors.push(`Item ${index + 1}: Name and Value are required`);
                invalidCards.push(card);
                return;
            }

            const isCustom = card.dataset.isCustom === 'true';
            const originalIndex = parseInt(card.dataset.itemIndex);
            const customId = card.dataset.customId;

            itemsToSave.push({
                itemData,
                isCustom,
                originalIndex,
                customId,
                card
            });
        });

        if (errors.length > 0) {
            AppFeedback.toast(`${errors.length} item${errors.length === 1 ? ' needs' : 's need'} a name and a value.`, 'error');
            document.dispatchEvent(new CustomEvent('editor-invalid', { detail: { cards: invalidCards } }));
            return;
        }

        // Initialize custom items array if needed
        if (!this.app.customItems[this.app.currentDimension]) {
            this.app.customItems[this.app.currentDimension] = [];
        }

        // Save each item
        itemsToSave.forEach(({ itemData, isCustom, originalIndex, customId, card }) => {
            if (isCustom && customId) {
                // Update existing custom item
                const customItems = this.app.customItems[this.app.currentDimension];
                const itemIndex = customItems.findIndex(item => item.customId === customId);

                if (itemIndex !== -1) {
                    // Preserve image data if it exists
                    if (customItems[itemIndex].imageData) {
                        itemData.imageData = customItems[itemIndex].imageData;
                    }
                    // Preserve isDeleted flag if it exists
                    if (customItems[itemIndex].isDeleted) {
                        itemData.isDeleted = customItems[itemIndex].isDeleted;
                    }
                    customItems[itemIndex] = { ...customItems[itemIndex], ...itemData };
                }
            } else {
                // For original items, create or update a custom override
                const existing = this.app.customItems[this.app.currentDimension].find(
                    item => item.originalIndex === originalIndex
                );

                if (existing) {
                    // Preserve image data if it exists
                    if (existing.imageData) {
                        itemData.imageData = existing.imageData;
                    }
                    // Update existing override/deletion marker
                    Object.assign(existing, itemData, {
                        isOverride: true,
                        isDeleted: false
                    });
                } else {
                    // Create new override
                    this.app.customItems[this.app.currentDimension].push({
                        ...itemData,
                        originalIndex: originalIndex,
                        isCustom: false,
                        isOverride: true,
                        isDeleted: false
                    });
                }
            }
        });

        this.saveCustomItems();
        this.renderDimensionMetadata();
        this.renderUnits();
        this.renderEditorItems();

        // Update dimension and unit descriptions in the main app
        if (this.app.dimensionDescription) {
            const dimensionDescOverride = this.dimensionOverrides[this.app.currentDimension]?.description;
            const dimensionDesc = dimensionDescOverride !== undefined
                ? dimensionDescOverride
                : (this.app.dimensionData?.dimension_description || '');

            if (dimensionDesc) {
                this.app.dimensionDescription.textContent = dimensionDesc;
                this.app.dimensionDescription.style.display = '';
            } else {
                this.app.dimensionDescription.textContent = '';
                this.app.dimensionDescription.style.display = 'none';
            }
        }

        // Update unit description
        this.app.updateUnitDescription();

        this.app.plot.updatePlot();
        document.dispatchEvent(new CustomEvent('editor-saved'));
    }

    deleteItem(event) {
        this.deleteCards([event.target.closest('.item-editor-card')]);
    }

    // Deletes these items. Their cards are removed directly, rather than re-rendering the list,
    // so unsaved edits in the other cards survive.
    deleteCards(cards) {
        if (!this.app.customItems[this.app.currentDimension]) {
            this.app.customItems[this.app.currentDimension] = [];
        }
        const customItems = this.app.customItems[this.app.currentDimension];

        cards.forEach(card => {
            const isCustom = card.dataset.isCustom === 'true';
            const customId = card.dataset.customId;

            if (isCustom && customId) {
                // Delete custom item completely
                const index = customItems.findIndex(item => item.customId === customId);
                if (index !== -1) {
                    customItems.splice(index, 1);
                }
            } else {
                // For original items, mark as deleted
                const originalIndex = parseInt(card.dataset.itemIndex);

                // Check if there's already an override or deletion marker
                const existing = customItems.find(item => item.originalIndex === originalIndex);

                if (existing) {
                    // Mark as deleted, preserve any override data
                    existing.isDeleted = true;
                } else {
                    // Create a deletion marker
                    customItems.push({
                        originalIndex: originalIndex,
                        isCustom: false,
                        isOverride: false,
                        isDeleted: true
                    });
                }
            }
            card.remove();
        });

        this.saveCustomItems();
        this.updateEditorHeader();
        this.app.plot.updatePlot();
        AppFeedback.toast(`Deleted ${cards.length} item${cards.length === 1 ? '' : 's'}. Undo all changes brings ${cards.length === 1 ? 'it' : 'them'} back.`);
    }

    compressImage(file, maxWidth = 800, maxHeight = 800, quality = 0.7) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    let width = img.width;
                    let height = img.height;

                    // Calculate new dimensions
                    if (width > height) {
                        if (width > maxWidth) {
                            height = (height * maxWidth) / width;
                            width = maxWidth;
                        }
                    } else {
                        if (height > maxHeight) {
                            width = (width * maxHeight) / height;
                            height = maxHeight;
                        }
                    }

                    canvas.width = width;
                    canvas.height = height;

                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    // Convert to JPEG (smaller than PNG) with quality setting
                    const compressedDataUrl = canvas.toDataURL('image/jpeg', quality);
                    resolve(compressedDataUrl);
                };
                img.onerror = reject;
                img.src = e.target.result;
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    async handleImageUpload(event, index) {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            AppFeedback.toast('Please select an image file', 'error');
            return;
        }

        try {
            // Compress image before storing
            const imageData = await this.compressImage(file);

            const card = event.target.closest('.item-editor-card');
            const isCustom = card.dataset.isCustom === 'true';
            const customId = card.dataset.customId;

            // Read current form values before updating
            const form = card.querySelector('.item-editor-form');
            const nameInput = form?.querySelector('input[name="name"]');
            const valueInput = form?.querySelector('input[name="value"]');
            const descriptionInput = form?.querySelector('textarea[name="description"]');
            const sourceInput = form?.querySelector('input[name="source"]');

            const currentName = nameInput?.value?.trim() || '';
            const currentValue = valueInput?.value ? parseFloat(valueInput.value) : 0;
            const currentDescription = descriptionInput?.value?.trim() || '';
            const currentSource = sourceInput?.value?.trim() || '';

            if (isCustom && customId) {
                const customItems = this.app.customItems[this.app.currentDimension] || [];
                let item = customItems.find(item => item.customId === customId);
                if (!item) {
                    // Item not found, create a new custom item entry with current form values
                    item = {
                        name: currentName,
                        value: currentValue,
                        description: currentDescription,
                        source: currentSource,
                        isCustom: true,
                        customId: customId,
                        imageData: imageData
                    };
                    customItems.push(item);
                } else {
                    // Update existing item with current form values and new image
                    item.name = currentName;
                    item.value = currentValue;
                    item.description = currentDescription;
                    item.source = currentSource;
                    item.imageData = imageData;
                }
                this.saveCustomItems();
                this.renderEditorItems();
            } else {
                // For original items, create an override
                const originalIndex = parseInt(card.dataset.itemIndex);
                if (!this.app.customItems[this.app.currentDimension]) {
                    this.app.customItems[this.app.currentDimension] = [];
                }

                const existingOverride = this.app.customItems[this.app.currentDimension].find(
                    item => item.originalIndex === originalIndex
                );

                if (existingOverride) {
                    existingOverride.imageData = imageData;
                } else {
                    this.app.customItems[this.app.currentDimension].push({
                        originalIndex: originalIndex,
                        isCustom: false,
                        isOverride: true,
                        imageData: imageData
                    });
                }
                this.saveCustomItems();
                this.renderEditorItems();
            }
        } catch (error) {
            console.error('Error processing image:', error);
            AppFeedback.toast('Error processing image. Please try a different image file.', 'error');
        }
    }

    removeImage(event, index) {
        event.preventDefault();
        event.stopPropagation();

        const card = event.target.closest('.item-editor-card');
        if (!card) {
            console.error('Could not find item card');
            return;
        }

        const isCustom = card.dataset.isCustom === 'true';
        const customId = card.dataset.customId;

        if (isCustom && customId) {
            const customItems = this.app.customItems[this.app.currentDimension] || [];
            const item = customItems.find(item => item.customId === customId);
            if (item) {
                delete item.imageData;
                this.saveCustomItems();
                this.renderEditorItems();
            }
        } else {
            const originalIndex = parseInt(card.dataset.itemIndex);
            if (isNaN(originalIndex)) {
                console.error('Invalid originalIndex:', card.dataset.itemIndex);
                return;
            }

            if (!this.app.customItems[this.app.currentDimension]) {
                this.app.customItems[this.app.currentDimension] = [];
            }

            // Look for an existing override (not a deletion marker)
            const override = this.app.customItems[this.app.currentDimension].find(
                item => item.originalIndex === originalIndex && !item.isDeleted
            );

            if (override) {
                // Mark image as explicitly removed by setting to null
                // Ensure isOverride is set so it's recognized as an override
                override.imageData = null;
                override.isOverride = true;
                override.isDeleted = false; // Ensure it's not marked as deleted
            } else {
                // Create a new override to mark the image as removed
                this.app.customItems[this.app.currentDimension].push({
                    originalIndex: originalIndex,
                    isCustom: false,
                    isOverride: true,
                    isDeleted: false,
                    imageData: null
                });
            }
            this.saveCustomItems();
            this.renderEditorItems();
        }
    }

    exportToYaml() {
        if (!this.app.dimensionData) return;

        // Create YAML structure with custom items merged
        const allItems = this.getAllItemsForEditor();

        // Sort items by value (smallest to largest) to match the plot order
        const sortedItems = [...allItems].sort((a, b) => {
            const valueA = parseFloat(a.value) || 0;
            const valueB = parseFloat(b.value) || 0;
            return valueA - valueB;
        });

        const yamlData = {
            dimension_description: this.app.dimensionData.dimension_description,
            units: this.app.dimensionData.units,
            items: sortedItems.map(item => {
                const itemData = {
                    name: item.name,
                    value: item.value,
                    description: item.description || '',
                    source: item.source || ''
                };
                // Note: imageData (base64) is too large for YAML, so we exclude it
                // Users would need to save images separately
                return itemData;
            })
        };

        const yamlText = jsyaml.dump(yamlData, { indent: 2 });
        this.showYamlModal('Export YAML', yamlText, false);
    }

    generateShareLink() {
        // Step 1: Collect what we want to share
        // We share current dimension data + overrides.
        const dataToShare = {
            customItems: {
                [this.app.currentDimension]: this.app.customItems[this.app.currentDimension] || []
            },
            dimensionOverrides: {
                [this.app.currentDimension]: this.dimensionOverrides[this.app.currentDimension]
            },
            unitOverrides: {
                [this.app.currentDimension]: this.unitOverrides[this.app.currentDimension]
            }
        };

        // Step 2: Strip image data (Base64) from the clones
        const stripImages = (obj) => {
            if (!obj || typeof obj !== 'object') return;
            if (Array.isArray(obj)) {
                obj.forEach(item => stripImages(item));
            } else {
                if (obj.imageData) {
                    delete obj.imageData;
                    this._hadStrippedImages = true;
                }
                for (const key in obj) {
                    if (Object.prototype.hasOwnProperty.call(obj, key)) {
                        stripImages(obj[key]);
                    }
                }
            }
        };

        this._hadStrippedImages = false;
        const cleanData = JSON.parse(JSON.stringify(dataToShare));
        stripImages(cleanData);

        // Step 3: Compress and generate link
        try {
            const jsonStr = JSON.stringify(cleanData);
            const compressed = LZString.compressToEncodedURIComponent(jsonStr);
            const shareUrl = `${window.location.origin}${window.location.pathname}${window.location.search}#data=${compressed}`;

            // Step 4: Copy to clipboard
            navigator.clipboard.writeText(shareUrl).then(() => {
                AppFeedback.confirm(this.sharePlotBtn, 'Link copied');
                if (this._hadStrippedImages) {
                    AppFeedback.toast('Uploaded images were left out to keep the link short.', 'info');
                }
            }).catch(err => {
                console.error('Clipboard error:', err);
                // Fallback: show in a modal or just console
                AppFeedback.toast('Could not copy to clipboard. Link available in console.', 'error');
                console.log('Share Link:', shareUrl);
            });
        } catch (e) {
            console.error('Sharing failed:', e);
            AppFeedback.toast('Sharing failed. The data might be too large.', 'error');
        }
    }

    showYamlImportModal() {
        this.showYamlModal('Import YAML', '', true);
    }

    showYamlModal(title, content, isImport) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('yaml-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'yaml-modal';
            modal.className = 'yaml-modal';
            modal.innerHTML = `
                <div class="yaml-modal-content">
                    <div class="yaml-modal-header">
                        <h3>${title}</h3>
                        <button class="yaml-modal-close" onclick="window.app.editor.closeYamlModal()">&times;</button>
                    </div>
                    <div id="yaml-drop-hint" class="yaml-drop-hint" style="display: none;">Drop YAML file here or paste content below</div>
                    <textarea id="yaml-textarea" class="yaml-textarea"></textarea>
                    <div class="yaml-modal-actions">
                        <button class="btn btn-secondary" onclick="window.app.editor.closeYamlModal()">Cancel</button>
                        <button class="btn btn-primary" onclick="window.app.editor.${isImport ? 'importYaml' : 'downloadYaml'}()">${isImport ? 'Import' : 'Download'}</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            // Close modal when clicking outside
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeYamlModal();
                }
            });
        }

        const header = modal.querySelector('.yaml-modal-header h3');
        const textarea = modal.querySelector('#yaml-textarea');
        const actionBtn = modal.querySelector('.yaml-modal-actions .btn-primary');
        const modalContent = modal.querySelector('.yaml-modal-content');
        const dropHint = modal.querySelector('#yaml-drop-hint');

        header.textContent = title;
        textarea.value = content;
        actionBtn.textContent = isImport ? 'Import' : 'Download';
        actionBtn.onclick = () => isImport ? this.importYaml() : this.downloadYaml();

        // Show/hide drag-and-drop hint based on mode
        if (dropHint) {
            dropHint.style.display = isImport ? 'block' : 'none';
        }

        // Set up drag-and-drop for import mode
        if (isImport) {
            this.setupYamlDragAndDrop(modalContent, textarea);
        } else {
            // Remove drag-and-drop handlers if switching to export mode
            this.removeYamlDragAndDrop(modalContent);
        }

        modal.style.display = 'block';
    }

    setupYamlDragAndDrop(modalContent, textarea) {
        // Remove existing handlers if any
        this.removeYamlDragAndDrop(modalContent);

        // Add drag-over class for visual feedback
        const handleDragOver = (e) => {
            e.preventDefault();
            e.stopPropagation();
            modalContent.classList.add('drag-over');
        };

        const handleDragLeave = (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Only remove class if we're leaving the modal content area
            if (!modalContent.contains(e.relatedTarget)) {
                modalContent.classList.remove('drag-over');
            }
        };

        const handleDrop = (e) => {
            e.preventDefault();
            e.stopPropagation();
            modalContent.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                // Check if it's a YAML file
                if (file.name.endsWith('.yaml') || file.name.endsWith('.yml') || file.type === 'text/yaml' || file.type === 'application/x-yaml') {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        textarea.value = event.target.result;
                    };
                    reader.onerror = () => {
                        AppFeedback.toast('Error reading file. Please try again.', 'error');
                    };
                    reader.readAsText(file);
                } else {
                    AppFeedback.toast('Please drop a YAML file (.yaml or .yml)', 'error');
                }
            }
        };

        // Store handlers for cleanup
        modalContent._dragOverHandler = handleDragOver;
        modalContent._dragLeaveHandler = handleDragLeave;
        modalContent._dropHandler = handleDrop;

        modalContent.addEventListener('dragover', handleDragOver);
        modalContent.addEventListener('dragleave', handleDragLeave);
        modalContent.addEventListener('drop', handleDrop);
    }

    removeYamlDragAndDrop(modalContent) {
        if (modalContent._dragOverHandler) {
            modalContent.removeEventListener('dragover', modalContent._dragOverHandler);
            modalContent._dragOverHandler = null;
        }
        if (modalContent._dragLeaveHandler) {
            modalContent.removeEventListener('dragleave', modalContent._dragLeaveHandler);
            modalContent._dragLeaveHandler = null;
        }
        if (modalContent._dropHandler) {
            modalContent.removeEventListener('drop', modalContent._dropHandler);
            modalContent._dropHandler = null;
        }
        modalContent.classList.remove('drag-over');
    }

    closeYamlModal() {
        const modal = document.getElementById('yaml-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    importYaml() {
        const textarea = document.getElementById('yaml-textarea');
        const yamlText = textarea.value;

        try {
            const importedData = jsyaml.load(yamlText);

            if (!importedData.items || !Array.isArray(importedData.items)) {
                AppFeedback.toast('Invalid YAML format: items array is required', 'error');
                return;
            }

            // Clear all existing items (both original and custom)
            this.deleteAllItems(false); // false = don't show confirmation, we're importing

            // Add all imported items as custom items
            importedData.items.forEach(item => {
                this.app.customItems[this.app.currentDimension].push({
                    ...item,
                    isCustom: true,
                    customId: `custom-${Date.now()}-${Math.random()}`
                });
            });

            this.saveCustomItems();
            this.closeYamlModal();
            this.renderEditorItems();
            this.app.plot.updatePlot();
            AppFeedback.toast('YAML imported successfully!', 'success');
        } catch (error) {
            AppFeedback.toast('Error parsing YAML: ' + error.message, 'error');
        }
    }

    downloadYaml() {
        const textarea = document.getElementById('yaml-textarea');
        const yamlText = textarea.value;

        const blob = new Blob([yamlText], { type: 'text/yaml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.app.currentDimension}_custom.yaml`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.closeYamlModal();
    }

    saveCustomItems() {
        try {
            const dataToSave = JSON.stringify(this.app.customItems);
            // Check approximate size (rough estimate: 1 character ≈ 1 byte for ASCII, but base64 is larger)
            const sizeInMB = new Blob([dataToSave]).size / (1024 * 1024);

            if (sizeInMB > 4) {
                console.warn(`Custom items data is ${sizeInMB.toFixed(2)}MB. Consider removing some images to avoid quota issues.`);
            }

            localStorage.setItem('customItems', dataToSave);

            // Save dimension and unit overrides separately
            const overridesToSave = {
                dimensionOverrides: this.dimensionOverrides,
                unitOverrides: this.unitOverrides
            };
            localStorage.setItem('dimensionUnitOverrides', JSON.stringify(overridesToSave));
        } catch (error) {
            if (error.name === 'QuotaExceededError') {
                AppFeedback.toast('Storage quota exceeded! The image data is too large. Please remove some images or use smaller images. Images are automatically compressed to 800x800px, but you may have too many images stored.', 'error');
                console.error('localStorage quota exceeded. Current data size:', new Blob([JSON.stringify(this.app.customItems)]).size / (1024 * 1024), 'MB');
            } else {
                console.error('Error saving custom items:', error);
                AppFeedback.toast('Error saving changes. Please try again.', 'error');
            }
        }
    }

    loadCustomItems() {
        const saved = localStorage.getItem('customItems');
        if (saved) {
            try {
                this.app.customItems = JSON.parse(saved);
            } catch (e) {
                console.error('Error loading custom items:', e);
                this.app.customItems = {};
            }
        }

        // Load dimension and unit overrides
        const overridesSaved = localStorage.getItem('dimensionUnitOverrides');
        if (overridesSaved) {
            try {
                const overrides = JSON.parse(overridesSaved);
                this.dimensionOverrides = overrides.dimensionOverrides || {};
                this.unitOverrides = overrides.unitOverrides || {};
            } catch (e) {
                console.error('Error loading dimension/unit overrides:', e);
                this.dimensionOverrides = {};
                this.unitOverrides = {};
            }
        }
    }

    // Called when dimension changes to refresh editor
    onDimensionChange() {
        if (this.editorContent && this.editorContent.style.display !== 'none') {
            this.renderDimensionMetadata();
            this.renderUnits();
            this.renderEditorItems();
        }
        // Update dimension selector when dimension changes
        this.updateDimensionSelector();
    }
}