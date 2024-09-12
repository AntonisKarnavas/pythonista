$('#type').on('change', function (e) {
    var optionSelected = $("option:selected", this);
    var valueSelected = this.value;
    if (valueSelected == 'mul') {
        $("#multiple").css('display', "block");
        $("#rw").css('display', "none");
        $("#gap").css('display', "none");

    } else if (valueSelected == 'rw') {
        $("#rw").css('display', "block")
        $("#multiple").css('display', "none")
        $("#gap").css('display', "none");
    } else if (valueSelected == 'gap') {
        $("#gap").css('display', "block");
        $("#rw").css('display', "none")
        $("#multiple").css('display', "none")
    } else {
        $("#multiple").css('display', "none")
        $("#rw").css('display', "none")
        $("#gap").css('display', "none")
    }
});


$('#test').on('change', function (e) {
    var optionSelected = $("option:selected", this);
    var valueSelected = this.value;
    if (valueSelected[0] == 'Q' || valueSelected[0] == 'C') {
        $("#chapter option").prop("selected", false);
        $('#chapter').find('option[value='+valueSelected.slice(0,-5)+']').attr('selected','selected');
    } else{
        $('#chapter option').eq(0).prop('selected', true);
        

    }
    $('#subchapter').css('display', "block");
    var select = $("#subchapter1")[0];
    if (valueSelected.slice(0,-5) == "Quickstart") {
        select.options[0] = new Option('Quickstart', 'Quickstart');
    } else if (valueSelected.slice(0,-5) == "Chapter1") {
        select.options[1] = new Option('Variables', 'Variables');
        select.options[2] = new Option('Data types', 'Data types');
        select.options[3] = new Option('Operators', 'Operators');

    } else if (valueSelected.slice(0,-5) == "Chapter2") {
        select.options[1] = new Option('Strings', 'Strings');
        select.options[2] = new Option('Numbers', 'Numbers');
        select.options[3] = new Option('Booleans', 'Booleans');

    } else if (valueSelected.slice(0,-5) == "Chapter3") {
        select.options[0] = new Option('Conditions', 'Conditions');

    } else if (valueSelected.slice(0,-5) == "Chapter4") {
        select.options[0] = new Option('Lists', 'Lists');

    } else if (valueSelected.slice(0,-5) == "Chapter5") {
        select.options[0] = new Option('For loops', 'For loops');

    } else if (valueSelected.slice(0,-5) == "Chapter6") {
        select.options[0] = new Option('While loops', 'While loops');

    } else if (valueSelected.slice(0,-5) == "Chapter7") {
        select.options[1] = new Option('Functions', 'Functions');
        select.options[2] = new Option('Lamdas', 'Lamdas');

    } else if (valueSelected.slice(0,-5) == "Chapter8") {
        select.options[0] = new Option('Classes', 'Classes');

    } else if (valueSelected.slice(0,-5)== "Chapter9") {
        select.options[0] = new Option('Inheritance', 'Inheritance');

    }else{
        $('#subchapter').css('display', "none");
    }
});


$('#chapter').on('change', function (e) {
    var optionSelected = $("option:selected", this);
    var valueSelected = this.value;
    var select = $("#subchapter1")[0];
    var optionSelected1 = $("#test option:selected");
    var valueSelected1 = optionSelected1.val()
    if (valueSelected1.slice(0,-5)!=valueSelected && valueSelected1.slice(0,1)!='B' && valueSelected1.slice(0,1)!='A' && valueSelected1.slice(0,1)!='E'){
        $("#test option:selected").removeAttr("selected");

        $('#test option').eq(0).prop('selected', true);
    }

    if (valueSelected != "Select chapter") {
        $('#subchapter').css('display', "block")
    }

    $("#subchapter1 option").each(function() {
        $(this).remove();
    });
    if (valueSelected == "Quickstart") {
        select.options[0] = new Option('Quickstart', 'Quickstart');
    } else if (valueSelected == "Chapter1") {
        select.options[1] = new Option('Variables', 'Variables');
        select.options[2] = new Option('Data types', 'Data types');
        select.options[3] = new Option('Operators', 'Operators');

    } else if (valueSelected == "Chapter2") {
        select.options[1] = new Option('Strings', 'Strings');
        select.options[2] = new Option('Numbers', 'Numbers');
        select.options[3] = new Option('Booleans', 'Booleans');

    } else if (valueSelected == "Chapter3") {
        select.options[0] = new Option('Conditions', 'Conditions');

    } else if (valueSelected == "Chapter4") {
        select.options[0] = new Option('Lists', 'Lists');

    } else if (valueSelected == "Chapter5") {
        select.options[0] = new Option('For loops', 'For loops');

    } else if (valueSelected == "Chapter6") {
        select.options[0] = new Option('While loops', 'While loops');

    } else if (valueSelected == "Chapter7") {
        select.options[1] = new Option('Functions', 'Functions');
        select.options[2] = new Option('Lamdas', 'Lamdas');

    } else if (valueSelected == "Chapter8") {
        select.options[0] = new Option('Classes', 'Classes');

    } else if (valueSelected == "Chapter9") {
        select.options[0] = new Option('Inheritance', 'Inheritance');

    }


});


$('#rightanswer').focus(function () {
    var select = $("#rightanswer")[0];

    $("#multiple > input").each(function (index) {
        if ($(this).val() != "") {
            i = index + 1
            select.options[i] = new Option('Answer ' + i + ': ' + $('#multiple' + i).val(), $('#multiple' + i).val());
        }

    });


});

$(document).ready(function () {
    $("#multiple").css('display', "none");
    $("#rw").css('display', "none");
    $("#gap").css('display', "none");
    $('#subchapter').css('display', "none");
});


$('#form').submit(function(e){
    e.preventDefault();
    question=$('#question').val();
    test=$('#test').val();
    chapter=$('#chapter').val();
    subchapter=$('#subchapter1').val();
    type=$('#type').val();
    if (type=='mul'){
        multiple=$('#multiple1').val();
        right=$('#rightanswer').val();
    }else if (type=='rw'){
        right=$('#rightanswerrw').val();
    }else if (type=='gap'){
        right=$('#rightquestiongap').val();
    }else{
        Swal.fire({
            icon: 'error',
            text: 'Please fill in all the required fields!'
        });
    }
    if (question=="" || question==null ||test==null || chapter==null || subchapter==null || type==null || right==null || right==""){
       
        Swal.fire({
            icon: 'error',
            text: 'Please fill in all the required fields!'
        });
    }else{
        if (type=='mul'){
            if ( multiple=="" || multiple==null){
                Swal.fire({
                    icon: 'error',
                    text: 'Please fill in all the required fields!'
                });
            }else{
                $(this).unbind('submit').submit()
            }
        }else{
            $(this).unbind('submit').submit()
        }
    }
    
    
});