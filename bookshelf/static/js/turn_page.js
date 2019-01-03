
window.onkeyup = function(e) {
    var key = e.keyCode ? e.keyCode : e.which;
    var next = $('#my-data').data('next');
    if(next != 'None')
    {
        next = next.replace(/\'/g,"\"");
        console.log(next)
        next = JSON.parse(next);
    }
    var prev = $('#my-data').data('prev');
    console.log(prev)
    if(prev != 'None')
    {
        prev = prev.replace(/\'/g,"\"");
        prev = JSON.parse(prev);
    }
    var book = $('#my-data').data('book');
    
    if (key == 39 && next != 'None') 
    {
        window.location = "/books/"+book+"/"+next.id;
    }
    else if (key == 37 && prev != 'None') 
    {
        window.location = "/books/"+book+"/"+prev.id;
    }
    
}

function drop_select(url)
{
    window.location = url
}