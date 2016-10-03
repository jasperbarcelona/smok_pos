function open_product_qty(id){
  $.post('/item/qty/get',{
      product_id:id
  },
  function(data){
    if (data['item_stock'] > 0){
      $('#quantity').val(1);
      $('#orderBtn').attr('disabled',false);
    }
    else{
      $('#quantity').val(0);
      $('#orderBtn').attr('disabled',true);
    }
    $('.qty-modal-header').html(data['item_name']);
    $('.product-details-container').html(data['template']);
  });
}

function add_product(){
  var qty = $('#quantity').val();
  var options_id = [];
  var options_name = [];

  options_id.push($('#Drink :selected').val());
  options_name.push($('#Drink :selected').text());

  options_id.push($('#Sauce :selected').val());
  options_name.push($('#Sauce :selected').text());

  test_func(qty,options_id,options_name)
}

function test_func(qty,options_id,options_name){
  $.post('/item/order/add',{
    qty:qty,
    options_id:options_id,
    options_name:options_name
  },
  function(data){
    $('.no-transaction').hide();
    $('#qtyModal').modal('hide');
    $('.transaction-panel-body').html(data['transaction_template']);
    $('#inventoryTab').html(data['inventory_template']);
    $('#currentTransactionPanel').find('.panel-footer').find('button').attr('disabled',false);
  });
}

function get_item_to_delete(id){
  $.post('/item/delete/get',{
      product_id:id
  },
  function(data){
    $('.delete-item-name').html(data['product_name']);
  });
}

function get_item_to_delete_transaction(id){
  $('#transactionInfoModal').modal('hide');
  $.post('/transaction/item/delete/get',{
      product_id:id
  },
  function(data){
    $('.delete-transaction-item-name').html(data['product_name']);
  });
}

function delete_from_transaction(id){
  $('#deleteFromTransactionModal').modal('hide');
  $.post('/transaction/item/delete',{
      product_id:id
  },
  function(data){
    $('#inventoryTab').html(data['inventory_template']);
    $('#transactionInfoBody').html(data['transaction_info_template']);
    $('#transactionInfoModal').modal('show');
  });
}


function delete_from_order(){
  $.post('/item/delete',
  function(data){
    if (data['item_count'] < 1){
          $('#currentTransactionPanel').find('.panel-footer').find('button').attr('disabled',true);
    }
    $('#deleteOrderModal').modal('hide');
    $('.transaction-panel-body').html(data['transaction_template']);
    $('#inventoryTab').html(data['inventory_template']);
  });
}

function cancel_transaction(){
  $.post('/transaction/cancel',
  function(data){
    $('#cancelTransactionModal').modal('hide');
    $('.transaction-panel-body').html(data);
    $('#currentTransactionPanel').find('.panel-footer').find('button').attr('disabled',true);
  });
}

function get_amount_tendered(){
  var customer_name = $('#customerName').val()
  $.post('/transaction/cash/amount',{
    customer_name:customer_name
  },
  function(data){
    $('#cashTotal').html(data['total']);
    $('#paymentSelectionModal').modal('hide');
    $('#cashTransactionModal').modal('show');
    $('#amountTendered').val('');
    $('#amountTendered').change();
    setTimeout(function() {
      $('#amountTendered').focus();
    }, 500);
  });
}

function compute_change(){
  var due = $('#cashTotal').html();
  var tendered = $('#amountTendered').val();
  if (tendered == ''){
    var change = 0
  }
  else{
    var change = parseFloat(tendered) - parseFloat(due);
  }
  if (parseFloat(tendered) >= parseFloat(due)){
    $('#changeDue').css('color','green');
    $('.changePhp').css('color','green');
    $('#tenderedDoneBtn').attr('disabled',false);
  }
  else{
    $('#changeDue').css('color','red');
    $('.changePhp').css('color','red');
    $('#tenderedDoneBtn').attr('disabled',true);
  }
  $('#changeDue').html(change);
}

function compute_pay_change(){
  var due = $('#payTotal').html();
  var tendered = $('#payAmountTendered').val();
  if (tendered == ''){
    var change = 0
  }
  else{
    var change = parseFloat(tendered) - parseFloat(due);
  }
  if (parseFloat(tendered) >= parseFloat(due)){
    $('#paychangeDue').css('color','green');
    $('.changePhp').css('color','green');
    $('#laterDoneBtn').attr('disabled',false);
  }
  else{
    $('#paychangeDue').css('color','red');
    $('.changePhp').css('color','red');
    $('#laterDoneBtn').attr('disabled',true);
  }
  $('#paychangeDue').html(change);
}

function pay_later(){
  var customer_name = $('#customerName').val()
  $.post('/transaction/finish/later',{
    customer_name:customer_name
  },
  function(data){
    if (data['status'] == 'success'){
      $('#paymentSelectionModal').modal('hide');
      $('#successModal').modal('show');
      $('.transaction-panel-body').html(data['transaction_template']);
      $('#historyTab').html(data['history_template']);
      $('#finishTransactionBtn').attr('disabled',true);
      $('#cancelTransactionBtn').attr('disabled',true);
    }
  });
}

function finish_cash_transaction(){
  var tendered = $('#amountTendered').val();
  $.post('/transaction/finish/cash',{
    tendered:tendered
  },
  function(data){
    if (data['status'] == 'success'){
      $('#cashTransactionModal').modal('hide');
      $('#successModal').modal('show');
      $('.transaction-panel-body').html(data['transaction_template']);
      $('#historyTab').html(data['history_template']);
      $('#finishTransactionBtn').attr('disabled',true);
      $('#cancelTransactionBtn').attr('disabled',true);
    }
  });
}

function show_existing_transactions(){
  $.post('/transaction/existing',
  function(data){
    $('#addToExistingModalBody').html(data);
    $('#paymentSelectionModal').modal('hide');
    $('#addToExistingModal').modal('show');
  });
}

function finish_pay_transaction(id){
  var tendered = $('#payAmountTendered').val();
  $.post('/transaction/finish/later/pay',{
    tendered:tendered
  },
  function(data){
    if (data['status'] == 'success'){
      $('#payTransactionModal').modal('hide');
      $('#transactionInfoModal').modal('hide');
      $('#successModal').modal('show');
      $('#historyTab').html(data['history_template']);
    }
  });
}

function refresh(){
  $.post('/order/list/update',
  function(data){
    $('.order-list-container').html(data);
    setTimeout(refresh,5000);
  });
}

function order_status(id,status){
  $.post('/order/status/update',{
    id:id,
    status:status
  },
  function(data){
    $('.order-list-container').html(data);
  });
}

function get_transaction_info(id){
  $.post('/transaction/info',{
    id:id,
  },
  function(data){
    $('#transactionInfoBody').html(data);
  });
}

function get_tendered_later(id){
  $.post('/transaction/later/amount',{
    id:id
  },
  function(data){
    $('#payTotal').html(data['total']);
    $('#payAmountTendered').val('');
    $('#payAmountTendered').change();
    setTimeout(function() {
      $('#payAmountTendered').focus();
    }, 500);
  });
}

function save_transaction_id(id){
  $.post('/transaction/id/save',{
    id:id
  },
  function(data){
    $('#confirmExistingName').html(data['customer_name']);
    $('#confirmExistingTotal').html('Php ' + data['total']);
    $('#addToExistingModal').modal('hide');
    $('#addToExistingConfirm').modal('show');
  });
}

function add_orders_to_existing(){
  $.post('/transaction/existing/add',
  function(data){
    $('#addToExistingConfirm').modal('hide');
    $('#historyTab').html(data);
    $('#successModal').modal('show');
    $('.transaction-panel-body').html(data['transaction_template']);
    $('#historyTab').html(data['history_template']);
    $('#finishTransactionBtn').attr('disabled',true);
    $('#cancelTransactionBtn').attr('disabled',true);
  });
}

function update_history(){
  $.post('/transaction/history/get',
  function(data){
    $('#historyTab').html(data['history_template']);
  });
}

function void_transaction(id){
  $.post('/transaction/void/id',{
    id:id
  },
  function(data){
  });
}

function void_transaction_confirmed(){
  $.post('/transaction/void/confirm',
  function(data){
    $('#historyTab').html(data['history_template']);
    $('#voidPasswordModal').modal('hide');
    $('#transactionInfoModal').modal('hide');
  });
}

function get_item_to_adjust(id){
  $.post('/item/adjust/get',{
    item_id:id
  },
  function(data){
    $('#currentStock').html(data['current_stock']);
    $('#adjustItemName').html(data['item_name']);
  });
}

function adjust_stock(){
  var plus = $('#addText').val();
  var minus = $('#subtractText').val();
  if (plus == ''){
    plus = 0;
  }
  if (minus == ''){
    minus = 0;
  }
  $.post('/item/adjust',{
    plus:plus,
    minus:minus
  },
  function(data){
    if (data['status'] == 'success'){
      $('#inventoryTab').html(data['inventory_template']);
      $('#adjustmentModal').modal('hide');
      $('#addText').val('');
      $('#subtractText').val('');
    }
  });
}