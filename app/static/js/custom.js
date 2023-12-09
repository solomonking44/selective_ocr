$(document).ready(function() {
    $('.toast').toast('show');

    $('#image_to_text').click(function(event) {
      event.preventDefault();
      $('#file').trigger('click');
    });
  
    $('#pdf_to_text').click(function(event) {
      event.preventDefault();
      $('#file').trigger('click');
    });

    $('#image_to_text_lg').click(function(event) {
      event.preventDefault();
      $('#file').trigger('click');
    });
  
    $('#pdf_to_text_lg').click(function(event) {
      event.preventDefault();
      $('#file').trigger('click');
    });

    $('#downloadFile').click(function(){
      $.ajax({
        
      })
    });

    $('#file').change(submitForm);
  
// 
// 
// TEST 1
// 
//     
    // $('#file').change(testing);

    // var testing = function(){
    //   alert('test 1')
    // }
    // 
//   
// 
// 
// 
//     
    function submitForm() {
      $('#file_form').off('submit').on('submit', function(event) {
        console.error('the form has been submitted');
        event.preventDefault();
        $('#sheet').toggleClass('d-none');
        var formData = new FormData(this)
        $.ajax({
            data: formData,
            type: 'POST',
            url: '/',
            contentType: false,
            processData: false,
        })
        .done(function(response){
            if(response != '0'){
                $('#sheet').toggleClass('d-none');
                $('#zohoLink').attr('href', response);
                $('#resultModal').modal('show');
            }
            else{
                $('#sheet').toggleClass('d-none');
                $('#errorMessage').text('Unsupported Upload Format');
                $('#resultModalFail').modal('show');                
                console.error('Unsupported Upload Format');
            }
        })
        .fail(function(xhr, status, error){
            console.error(xhr.responseText);
            console.error(error);
            console.error(status);
        });

      });
      $('#file_form').submit();
    }
  
});

