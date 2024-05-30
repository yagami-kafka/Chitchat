const base_url = window.location.origin;
const redirectToChat = (u_id,csrf) =>{
    console.log(csrf)
    var chat_url = base_url+'/chat/create_or_return_private_chat/';
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: chat_url,
        data: {
            'csrfmiddlewaretoken': csrf,
            'second_user_id': u_id,
        },
        timeout: 5000,
        success: (data)=>{
            console.log("SUCCESS chat",data);
            if(data['response'] == "Successfully got the chat."){
				OnGetOrCreateChatroomSuccess(u_id)
            }
            else if(data['response']!=null){
                alert(data.response);
            }
        },
        error: (data)=>{
            console.error("ERROR....",data)
            // showClientErrorModal(data)
            alert("Something went wrong.")
        },
    });
}
const OnGetOrCreateChatroomSuccess = (u_id)=>{
    var url = base_url+"/chat/?t_id=" + u_id
    var win = window.location.replace(url)
    // window.open(url) // for new tab
    win.focus()
}
