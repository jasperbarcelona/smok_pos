$(document).ready(function(){
    
    var item = $('.item');
    item.css('height',item.width() - 10);

    $('#qtyPlus').on('click', function () {
        var current_qty = $('#quantity').val();
        var current_stock = $('#qtyStock').html();
        
        if (parseInt(current_qty) < parseInt(current_stock)){
            var new_qty = parseInt(current_qty) + 1;
            $('#quantity').val(new_qty);
        }
    });

    $('#qtyMinus').on('click', function () {
        var current_qty = $('#quantity').val();
        if (current_qty > 1){
            var new_qty = parseInt(current_qty) - 1;
            $('#quantity').val(new_qty);
        }
    });

    $('#customerName').on('keyup', function () {
        if ($('#customerName').val() != ''){
            $('.payment-selection-cover').hide();
        }
        else{
            $('.payment-selection-cover').show();
        }
    });

    $('#amountTendered').on('keyup', function () {
        compute_change();
    });

    $('#amountTendered').on('change', function () {
        compute_change();
    });

    $('#payAmountTendered').on('keyup', function () {
        compute_pay_change()
    });

    $('#payAmountTendered').on('change', function () {
        compute_pay_change()
    });


    $('#cashTransactionModal').on('hidden.bs.modal', function () {
        $('#amountTendered').val('');
        $('#amountTendered').change();
    });

    $('#paymentSelectionModal').on('shown.bs.modal', function () {
        $('#customerName').focus();
    });

    $('#addToExisting').on('click', function () {
        show_existing_transactions();
    });

    $('#paymentSelectionModal').on('hidden.bs.modal', function () {
        $('#customerName').val('');
        $('.payment-selection-cover').show();
    });

})