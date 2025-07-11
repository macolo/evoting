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
        }
    }
    
    // Initial state and event listener
    var voteTypeField = document.getElementById('id_vote_type');
    if (voteTypeField) {
        toggleDefaultValueField();
        voteTypeField.addEventListener('change', toggleDefaultValueField);
    }
});
