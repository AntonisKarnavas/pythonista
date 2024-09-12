$('.btn').click(function () {
    $(this).toggleClass("click");
    $('.sidebar').toggleClass("show");
    $('.image2').toggleClass("rotate");
});


$('.feat-btn').click(function () {
    $(this).siblings('ul').toggleClass("show");
    $(this).children('.image').toggleClass("rotate");
});


$('.li').click(function () {
    $(this).addClass("active").siblings().removeClass("active");
});

$('.inner-li').mouseover(
    function () {
        $(this).children().css('color', '#8167a9');
    }
);

$('.inner-li').mouseout(
    function () {
        $(this).children().css('color', '#e6e6e6');
    }
);




$(document).ready(function () {
    $('.text').slideUp();
    $(".button").each(function (index) {
        $(this).attr('name', $(this).parent().parent().parent().parent().attr('id'))
    });
    $(".test-btn").each(function (index) {
        $(this).attr('name', $(this).parent().parent().parent().parent().attr('id') + '_test')
    });
    $(".right").click(function () {
        if ($(this).hasClass('rotate')) {
            $(this).removeClass('rotate');
            $(this).parent().parent().siblings('.rest').children('.col-12').children('.text').slideUp();
        } else {
            $(this).addClass('rotate');
            $(this).parent().parent().siblings('.rest').children('.col-12').children('.text').slideDown();
           
        }

    });

});

$(".right").hover(function () {
    $(this).css('cursor', 'pointer');
});

$(".inner-li").click(function () {
    move = $('#' + $(this).children('.inner-a').text().replace(/ /g, '')).children('div.row.first').children().eq(1).children('img.right');
    $('.text').not(move.parent().parent().siblings('.rest').children('.col-12').children('.text')).slideUp();
    $('.right').not(move).removeClass('rotate');
    $('.btn').removeClass("click");
    $('.sidebar').removeClass("show");
    $('.image2').removeClass("rotate");
    if (!($('#' + $(this).children('.inner-a').text().replace(/ /g, '')).children().eq(0).hasClass('disabled'))) {
        move.parent().parent().siblings('.rest').children('.col-12').children('.text').slideDown();
        move.addClass('rotate');

    } else {
        animateCSS('#' + $(this).children('.inner-a').text().replace(/ /g, ''), 'shakeX');
    }
    $([document.documentElement, document.body]).animate({
        scrollTop: $('#' + $(this).children('.inner-a').text().replace(/ /g, '')).offset().top - 100
    });

});


function validate() {
    $(this).removeClass("onclic");
    $(this).addClass("validate");
}
function callback() {

    $(this).removeClass("validate");
}




$('.button').click(function () {
    var $btn = $(this);
    $btn.addClass("onclic");
    completed = $(this).attr('name');
    $.ajax({
        data: {
            chapter: completed
        },
        type: 'POST',
        url: '/chapters'
    })
        .done(function (data) {
            if (data.success) {
                $btn.delay(1500).queue(validate).queue(callback).attr('disabled', 'disabled').css('pointer-events', 'none');
                $btn.siblings(".test-btn").addClass("visible");
            } else if (data.error) {
                Swal.fire({
                    icon: 'error',
                    text: data.error
                });
            }

        });

})


function redirect(a) {
    window.location.href = "tests?test=" + a.name
}


function format(chapters, tests, all_chapters, all_tests) {
    for (let i = 0; i < all_chapters.length; i++) {
        if (all_chapters[i] == "Basics" || all_chapters[i] == "Advanced" || all_chapters[i] == "Expert") {
            all_chapters.splice(i, 1)
            i -= 1
        }
    }
    var elmts = chapters.filter(f => all_chapters.includes(f));
    if (elmts.length > 0) {
        $('#Quickstart').children('.rest').children().eq(0).children('.text').children(".button").addClass("validate").attr('disabled', 'disabled').css('pointer-events', 'none');
        $('#Quickstart').children('.rest').children().eq(0).children('.text').children(".test-btn").addClass("visible");

    }
    for (let i = 0; i < elmts.length; i++) {
        $('#' + elmts[i]).children('.rest').children().eq(0).children('.text').children(".button").addClass("validate").attr('disabled', 'disabled').css('pointer-events', 'none');
        $('#' + elmts[i]).children('.rest').children().eq(0).children('.text').children(".test-btn").addClass("visible");
    }

    for (let i = 1; i < all_chapters.length; i++) {
        if (!tests.includes(all_chapters[i] + "_test") && !tests.includes(all_chapters[i - 1] + "_test")) {
            $('#' + all_chapters[i]).children().addClass('disabled');
            $('#' + all_chapters[i]).children('.first').children().eq(1).children('img.right').attr('src', "../static/images/lock.png").addClass("disable");
        }
    }

    for (let i = 0; i < tests.length; i++) {
        $('#' + tests[i].slice(0, -5)).children().eq(1).children().children().children('.test-btn').html("Test taken").attr('disabled', 'disabled').css('pointer-events', 'none');
    }



}
