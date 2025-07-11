(function($) {
    'use strict';
    
    function toggleDefaultValueField() {
        var voteType = $('#id_vote_type').val();
        var defaultValueRow = $('.field-default_value');
        
        if (voteType === 'short_text') {
            defaultValueRow.show();
        } else {
            defaultValueRow.hide();
            // Clear the field when hidden
            $('#id_default_value').val('');
        }
    }
    
    $(document).ready(function() {
        // Initial state
        toggleDefaultValueField();
        
        // Listen for changes to vote_type
        $('#id_vote_type').change(function() {
            toggleDefaultValueField();
        });
    });
})(django.jQuery);
