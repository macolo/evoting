document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    function toggleDefaultValueField() {
        var voteTypeField = document.getElementById('id_vote_type');
        var defaultValueRow = document.querySelector('.field-default_value');
        
        if (!voteTypeField || !defaultValueRow) {
            return;
        }
        
        var voteType = voteTypeField.value;
        
        if (voteType === 'short_text') {
            defaultValueRow.style.display = '';
        } else {
            defaultValueRow.style.display = 'none';
            // Clear the field when hidden
            var defaultValueField = document.getElementById('id_default_value');
            if (defaultValueField) {
                defaultValueField.value = '';
            }
        }
    }
    
    // Initial state
    toggleDefaultValueField();
    
    // Listen for changes to vote_type
    var voteTypeField = document.getElementById('id_vote_type');
    if (voteTypeField) {
        voteTypeField.addEventListener('change', toggleDefaultValueField);
    }
});
