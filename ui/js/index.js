
$(function(){
    var ipsettings = undefined;

    var netmask2CIDR = (netmask) => (netmask.split('.').map(Number)
      .map(part => (part >>> 0).toString(2))
      .join('')).split('1').length -1;

    var CIDR2netmask = (bitCount) => {
        var mask=[];
        for(var i=0;i<4;i++) {
            var n = Math.min(bitCount, 8);
            mask.push(256 - Math.pow(2, 8-n));
            bitCount -= n;
        }
        return mask.join('.');
    }

    function showHideFormFields() {
        var mode = $(this).find(':selected').val();
        // start off with all fields hidden
        $('#ip-address-group').addClass('hidden');
        $('#netmask-group').addClass('hidden');
        $('#gateway-group').addClass('hidden');
        if(mode === 'auto') {
            return; // nothing to do
        }
        if(mode === 'manual') {
            $('#ip-address-group').removeClass('hidden');
            $('#netmask-group').removeClass('hidden');
            $('#gateway-group').removeClass('hidden');
            return;
        } 
        if(mode === 'local') {
            return; // nothing to do
        } 
    }

    $('#mode-select').change(showHideFormFields);


    $.get("/ipsettings", function(data){
        console.log('debugrob data=',data);
        if(data.length === 0){
            $('.before-submit').hide();
            $('#no-settings-message').removeClass('hidden');
        } else {
            ipsettings = JSON.parse(data);
            $('#mode-select').val(ipsettings.method)
            $('#ip-address').val(ipsettings.addresses[0][0])
            $('#netmask').val(CIDR2netmask(ipsettings.addresses[0][1]))
            $('#gateway').val(ipsettings.addresses[0][2])
            jQuery.proxy(showHideFormFields, $('#mode-select'))();
        }
    });

    //TODO: Validate IP Address and netmask
    $('#connect-form').submit(function(ev){
        var netmask_text = $('#netmask').val()
        $('#netmask').val(netmask2CIDR(netmask_text))
        $.post('/connect', $('#connect-form').serialize(), function(data){
            $('.before-submit').hide();
            $('#submit-message').removeClass('hidden');
            $(location).delay(2000).attr('hostname', $('#ip-address').val());
        });
        $('#netmask').val(netmask_text)
        ev.preventDefault();
    });
});
