document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    var previousVoteType = null;
    
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
            // Only clear the field when changing FROM short_text TO another type
            if (previousVoteType === 'short_text') {
                var defaultValueField = document.getElementById('id_default_value');
                if (defaultValueField) {
                    defaultValueField.value = '';
                }
            }
        }
        
        previousVoteType = voteType;
    }
    
    // Set initial previous vote type and toggle field
    var voteTypeField = document.getElementById('id_vote_type');
    if (voteTypeField) {
        previousVoteType = voteTypeField.value;
        toggleDefaultValueField();
        voteTypeField.addEventListener('change', toggleDefaultValueField);
    }
});
