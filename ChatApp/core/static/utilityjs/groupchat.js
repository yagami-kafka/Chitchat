var groupChatWebSocket = null;
var groupThreadId = null;

function onSelectGroup(threadId,ele){
    // createOrReturnPrivateChat(threadId)
    var nextURL = window.location.origin+'/chat/?gt_id='+threadId;
    var nextTitle = 'My new page title';
    var nextState = { additionalInformation: 'Updated the URL with JS' };

    // This will create a new entry in the browser's history, without reloading
    window.history.pushState(nextState, nextTitle, nextURL);

    // This will replace the current entry in the browser's history, without reloading
    window.history.replaceState(nextState, nextTitle, nextURL)
    removeActiveThreadFriend();

    setActiveThreadFriend(threadId);
    $(".user-chat").addClass("user-chat-show");
    groupChatWebSocketSetup(threadId);


}

function closegroupWebSocket(){
    if(groupChatWebSocket != null){
        groupChatWebSocket.close()
        groupChatWebSocket = null
        clearChat();
        showLoader();
        setPageNumber("1");
        disableChatHistoryScroll();
    }
}
let current_user =JSON.parse(document.getElementById('logged_in_user').textContent);

var updateWs = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/tu/'
    + current_user.id
    + '/'
)

// var indivWs = new WebSocket(
//     'ws://'
//     + window.location.host
//     + '/ws/a_&_i/'
//     + current_user.id
//     + '/'
// ) 

updateWs.onmessage = function(e){
    var data = JSON.parse(e.data);
    if(data.thread_details){
        console.log("update ws ko thread details cha")
        update_thread_list_view(data.thread_details);
        gk();
    }
    if(data.user_action){
        closegroupWebSocket();
        clearOnLeave();
    }

}

$('#test_thread').on('click',function(){
    fetch('http://localhost:8000/chat/test_thread')
    .then(response => response.json())
    .then(data =>{
                console.log(data)
    })
})

function groupChatWebSocketSetup(thread_id){
    groupThreadId = thread_id
    // closeWebSocket();
    clearChat();
    showLoader();
    setPageNumber("1");
    disableChatHistoryScroll();
    closegroupWebSocket();
    
    groupChatWebSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/groupchat/'
        + groupThreadId
        + '/'
    )

    groupChatWebSocket.onmessage = function(e){
        const data = JSON.parse(e.data);
        console.log(data)
		displayChatroomLoadingSpinner(data.display_progress_bar)

        if(data.error){
            console.error(data.error + ": "+data.message)
            showClientErrorModal(data.message)
            return;
        }

        if (data.joining_group_chat){
            if(data['requested_by'] ==logged_user.username){
                var secret_key = document.getElementById('topbar_otheruser_name');
                secret_key.removeAttribute('data-val');
                thread_distinguish.innerHTML = data.thread_type;
                getGroupChatInfo();
                showLoader();
                getGroupThreadMessages(true);
                hideLoader();
                enableChatHistoryScroll();
            }
        }


        if(data.command =='group_chat'){
        if(data.msgTypeList && data.msgTypeList.includes(data.msg_type)){
                if(data.action && data.actionList.includes(data.action)){
                    let members_info = data['members_info']
                    if(data.removee){
                        if(data.removee.username === logged_user['username']){
                            Toast.fire({
                                icon: 'warning',
                                title: 'You have been removed from the group'
                            })
                        clearOnLeave();
                        closegroupWebSocket();
                        }else{
                            Toast.fire({
                                icon: 'warning',
                                title: `${members_info['admin_username']} has removed ${data.removee.first_name} from the group.`
                            })
                        group_members_display(members_info['members'],members_info['admin_id'],members_info['admin_username'],members_info['thread_id']);
                        }

                    }else if(data.added_members){
                        data.added_members.forEach(member => {
                            if(member.username === logged_user['username']){
                                Toast.fire({
                                    icon: 'success',
                                    title: `You have been added to the group ${members_info.group_name}.`
                                })
                            }
                            else{
                                Toast.fire({
                                    icon: 'success',
                                    title: `${members_info.admin_username} has added ${member.first_name} in the group.`
                                })
                            }
                            
                        });
                    group_members_display(members_info['members'],members_info['admin_id'],members_info['admin_username'],members_info['thread_id']);

                    }else if(data.left_user){
                        Toast.fire({
                            icon: 'warning',
                            title: `${data.left_user.first_name} ${data.left_user.last_name} has left the group.`
                        })
                    group_members_display(members_info['members'],members_info['admin_id'],members_info['admin_username'],members_info['thread_id']);
                    }
                }
            
            console.log("hey there")
            $.ajax({
                type: "GET",
                url: window.location.origin+'/chat/chat_thread_list/',
                timeout: 5000,
                success: (data) => {
                    update_thread_list_view(data);
                    gk();
                }
            });
           let active_grp_thread =  document.getElementById('topbar_otheruser_name').dataset.group_thread_id
            if(active_grp_thread == data.group_thread_id){
            appendGroupChatMessage(data,false,true);
            }
        }

    }

        if(data.group_chat_info){
            if(groupThreadId == data.group_thread_id){
                
            my_info = JSON.parse(data['group_chat_info'])
            onReceivingGroupChatInfo(my_info);
            }
        }
        if(data.messages_response){
            onReceivingGroupMessagesResponse(data.messages_metadata,data.new_page_number,data.firstAttempt);
        }
        // if(data.command == 'is_typing'){
        //     displayTyping(data.grp_display_typing)
        // }
    }

    groupChatWebSocket.addEventListener("open", function(e){
        // join chat room
        if(unsafe_authenticated){
            groupChatWebSocket.send(JSON.stringify({
                "command": "join",
                "requested_by": logged_user.username,
            }));
        }
    })
    groupChatWebSocket.onopen = function(e){
        // console.log("i am connected to group")
    }
    groupChatWebSocket.onclose = function(){
        console.error("group chat socket closed.")
    }

    if(groupChatWebSocket.readyState == WebSocket.OPEN){
        console.log("Group chat socket open")
    }else if(groupChatWebSocket.readyState == WebSocket.CONNECTING){
        console.log("Group chat socket connecting...")
    }
}



function groupChatSend(chat_message){
    groupChatWebSocket.send(
        JSON.stringify({
            "command":"group_chat",
            "message": chat_message,
            "message_type": "text",
        })
    )
}

function getGroupThreadMessages(firstAttempt=false){
    var pageNumber = document.getElementById("page_number_id").innerHTML
    if(pageNumber!= '-1'){
        setPageNumber('-1');

        groupChatWebSocket.send(JSON.stringify(
            {
                'command':'request_group_messages_data',
                'page_number': pageNumber,
                'firstAttempt':firstAttempt,
            }
        ));
    }
}

function getGroupChatInfo(){
    
    groupChatWebSocket.send(JSON.stringify({
        'command': 'get_group_chat_info',
    }))
}


function clearOnLeave(){
    document.getElementById('id_other_username').textContent = ''
    document.getElementById('topbar_otheruser_name').textContent = '';
    document.getElementById('topbar_otheruser_name').href ='#';
    document.getElementById('topbar_otheruser_name').removeAttribute('data-other_user_id');
    document.getElementById('topbar_otheruser_name').removeAttribute('data-group_thread_id');
    document.getElementById('topbar_otheruser_name').removeAttribute('data-pvt_thread_id');
    document.getElementById('topbar_otheruser_name').dataset.group_thread_id = '';

    document.getElementById('other_user_info').href ='#';
    document.getElementById('other_user_profile_image').classList.remove("d-none");
    document.getElementById('sidebar_simplebar_about').innerHTML = "Customize Chat";
    document.getElementById('aboutprofile').innerHTML = ``
    document.getElementById('change_group_name').setAttribute("value",'');
    document.getElementById('change_group_name').setAttribute("data-threadid",'');
    $('#group_members').html('');
    console.log("clear on leave called")
    $('#group_members_wrapper').addClass('d-none');
    console.log("clear on leave called after d-none")
    let image = '/media/user_photos/nouser.jpg'
    preloadImage(image, 'other_user_profile_image')
    preloadImage(image,'topbar_otheruser_image')
}


function onReceivingGroupChatInfo(group_chat_info){
    document.getElementById('id_other_username').innerHTML = group_chat_info['group_name']
    document.getElementById('topbar_otheruser_name').innerHTML = group_chat_info['group_name'];
    document.getElementById('topbar_otheruser_name').href ='#';
    document.getElementById('topbar_otheruser_name').removeAttribute('data-other_user_id');
    document.getElementById('topbar_otheruser_name').removeAttribute('data-pvt_thread_id');
    document.getElementById('topbar_otheruser_name').dataset.group_thread_id = group_chat_info['thread_id'];

    document.getElementById('other_user_info').href ='#';
    document.getElementById('other_user_profile_image').classList.remove("d-none");
    document.getElementById('sidebar_simplebar_about').innerHTML = "Customize Chat";
    document.getElementById('aboutprofile').innerHTML = `
                                        <div class="accordion-body">
                                        <a href="#" data-bs-toggle="modal" data-bs-target="#gc_name_change_modal">
                                            <div class="card p-2 border mb-2 gc-settings">
                                                <div class="d-flex align-items-center">
                                                    <div class="flex-1">
                                                        <div class="text-start">
                                                            <h5 class="font-size-14 mb-1">Change Chat Name</h5>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>  
                                        </a>

                                        <a href="#" data-bs-toggle="modal" data-bs-target="#gc_photo_change_modal">
                                        <div class="card p-2 border mb-2 gc-settings" id="change_photo_div">
                                            <div class="d-flex align-items-center">
                                                <div class="flex-1">
                                                    <div class="text-start">
                                                    <h5 class="font-size-14 mb-1">Change Group Photo</h5>
                                                    </div>
                                                </div>
                                            </div>
                                        </div> 
                                        </a>
                                                                              
                                        </div>`
    document.getElementById('change_group_name').setAttribute("value",group_chat_info['group_name']);
    document.getElementById('change_group_name').setAttribute("data-threadid",group_chat_info['thread_id']);

    group_members_display(group_chat_info['members'],group_chat_info['admin_id'],group_chat_info['admin_username'],group_chat_info['thread_id']);

    preloadImage(group_chat_info['image'], 'other_user_profile_image')
    preloadImage(group_chat_info['image'],'topbar_otheruser_image')
}

var onReceivingGroupMessagesResponse = (messages,new_page_number,firstAttempt)=>{
    if(messages!= null && messages != 'undefined' && messages!="None"){
        setPageNumber(new_page_number);
        messages.forEach(element => {
            appendGroupChatMessage(element, true,false);
            
        });
        if(firstAttempt){
            scrollToBottom();
        }
        
    }else{
        paginationKhattam();
    }
}
function appendGroupChatMessage(data, maintainPosition, isNewMessage){
    messageType = data['msg_type']
    msg_id = data['msg_id']
    message = data['message']
    uName = data['username']
    user_id = data['user_id']
    profile_image = data['profile_image']
    timestamp = data['natural_timestamp']
    new_chat_name = data['new_chat_name']
    var msg = "";
    var username = ""

    // determine what type of msg it is
    switch (messageType) {
        case 0:
            // new chatroom msg
            username = uName + ": "
            msg = message + '\n'
            createChatMessageElement(data, maintainPosition, isNewMessage)
            break;
        case 1:
            // User added to chat
            createConnectedDisconnectedElement(message, msg_id, profile_image, user_id)
            break;
        case 2:
            // User left chat
            createConnectedDisconnectedElement(message, msg_id,profile_image, user_id)
            break;
        case 3:
            //Chat photo changed
            createConnectedDisconnectedElement(message, msg_id,profile_image, user_id);
            break;
        case 4:
            //Chat name changed
            $('#topbar_otheruser_name').html(new_chat_name);
            $('#id_other_username').html(new_chat_name)
            createConnectedDisconnectedElement(message,msg_id,profile_image,user_id);
            break;
        default:
            console.log("Unsupported message type!");
            return;
    }
}

function createChatMessageElement(data,maintainPosition, isNewMessage){
    msg_id= data['msg_id'];
    user_id = data['user_id'];
    message_content = data['message_content']
    sender_fname = data['first_name'];
    sender_lname = data['last_name'];
    msg_timestamp = data['natural_timestamp'];
    profile_image = data['profile_image'];
    username = data['username'];
    
    //get the parent ul element
    var chat_history = document.getElementById('id_chat_log');
    
    //create the child elements
    var newMessageBlock = document.createElement('div');
    var conversation_list_div = document.createElement('div');
    var chat_avatar_div = document.createElement('div');
    var user_chat_content_div = document.createElement('div');
    var ctext_wrap_div = document.createElement('div');
    var ctext_wrap_content_div = document.createElement('div');
    var new_message_content = document.createElement('p');
    var message_timestamp_p = document.createElement('p');
    var conversation_name_div = document.createElement('div');

    //add class to every created element
    conversation_list_div.classList.add('conversation-list');
    chat_avatar_div.classList.add('chat-avatar');
    user_chat_content_div.classList.add('user-chat-content');
    ctext_wrap_div.classList.add('ctext-wrap');
    ctext_wrap_content_div.classList.add('ctext-wrap-content');
    new_message_content.classList.add('mb-0')
    message_timestamp_p.classList.add('chat-time','mb-0');
    conversation_name_div.classList.add('conversation_name_div');
    var profileImage = document.createElement('img');
    profileImage.dataset.sender_id = user_id;
    profileImage.classList.add('clickable_cursor');
    profileImage.addEventListener('click',(e)=>{
        selectUser(profileImage.dataset.sender_id);
    });
    var sender_profile_image_id = "sender_profile_image_"+msg_id;
    profileImage.id = sender_profile_image_id;
    //rewrite the content of the created element message,timestamp and name
    new_message_content.innerHTML = validateText(message_content) ;
    message_timestamp_p.innerHTML = msg_timestamp
    conversation_name_div.innerHTML = sender_fname +" "+ sender_lname
    //check if the sender is the logged in user
        //append elements in order
        ctext_wrap_content_div.append(new_message_content,message_timestamp_p);
        ctext_wrap_div.appendChild(ctext_wrap_content_div);
        user_chat_content_div.append(ctext_wrap_div,conversation_name_div);
        chat_avatar_div.appendChild(profileImage);
        conversation_list_div.append(chat_avatar_div,user_chat_content_div)
        newMessageBlock.appendChild(conversation_list_div)
    if(user_id == logged_user.id && username == logged_user.username){
        // new_message_content.classList.add('')
        newMessageBlock.classList.add('sent','right');

    }else{
        // new_message_content.classList.add('')
        newMessageBlock.classList.add('replies');
    }
    //append message based on if it is instant message or the whole chunk of previous messages

    if(isNewMessage){
        chat_history.insertBefore(newMessageBlock,chat_history.firstChild);
    }else{
        chat_history.appendChild(newMessageBlock);
    }
    if(!maintainPosition){
        scrollToBottom();
    }
    preloadImage(profile_image,sender_profile_image_id);
}

function createConnectedDisconnectedElement(msg, msd_id, profile_image, user_id){
    var chatLog = document.getElementById("id_chat_log")

    var newMessageDiv = document.createElement("div")
    newMessageDiv.classList.add("d-flex")
    newMessageDiv.classList.add("flex-row")
    newMessageDiv.classList.add("message-container")

    var profileImage = document.createElement("img")
    profileImage.addEventListener("click", function(e){
        selectUser(user_id)
    })
    profileImage.classList.add("profile-image")
    profileImage.classList.add("rounded-circle")
    profileImage.classList.add("img-fluid")
    profileImage.src = "{% static 'codingwithmitch/dummy_image.png' %}"
    var profile_image_id = "id_profile_image_" + msg_id
    profileImage.id = profile_image_id
    newMessageDiv.appendChild(profileImage)

    var usernameSpan = document.createElement("span")
    usernameSpan.innerHTML = msg
    usernameSpan.classList.add("username-span")
    usernameSpan.addEventListener("click", function(e){
        selectUser(user_id)
    })
    newMessageDiv.appendChild(usernameSpan)

    chatLog.insertBefore(newMessageDiv, chatLog.firstChild)

    preloadImage(profile_image, profile_image_id)
 }


 function test_url(mid){
    const nextURL = window.location.origin+'/account/profile/'+mid;
    const nextTitle = 'My new page title';
    const nextState = { additionalInformation: 'Updated the URL with JS' };

    // This will create a new entry in the browser's history, without reloading
    window.history.pushState(nextState, nextTitle, nextURL);

    // This will replace the current entry in the browser's history, without reloading
    window.history.replaceState(nextState, nextTitle, nextURL)
}
function group_members_display(members,admin_id,admin_username,group_thread_id){
    $('#group_members_wrapper').removeClass("d-none");
    $('#sidebar_simplebar_grp_members').html('Chat Members');
    $('#group_members').html('');
    var member_type;
    var is_self;
    var can_kick;
    if(members){
    members.forEach(member => {
        if(member.id == admin_id && member.username ==admin_username){
            member_type = 'Admin';
        }else{
            member_type = 'Member';
        }
        //determine if is_self = true or false
        is_self = true ? logged_user.id == member.id : false;

        //determine if the currently logged in user can kick the members or not; to kick others you have to be admin/creator of that group
        if(logged_user.id == admin_id && logged_user.username ==admin_username){
            member_type == 'Member' ? can_kick = true : can_kick = false; 
        }else if(logged_user.id!=admin_id){
            can_kick = false;
        }    
        document.getElementById('group_members').innerHTML +=
        `<div class="card p-2 border mb-2">
        <div class="d-flex align-items-center">
            <div class="avatar-sm me-3 ms-0">
                <div class="avatar-title bg-soft-primary text-primary rounded font-size-20">
                    <img src="${member.profile_image}" alt="members" class="avatar-sm rounded-circle">
                </div>
            </div>
            <div class="flex-1">
                <div class="text-start">
                    <h5 class="font-size-14 mb-1">${member.first_name} ${member.last_name}</h5>
                    <p class="text-muted font-size-13 mb-0"> ${member_type}</p>
                </div>
            </div>
    
            <div class="ms-4 me-0">
                <ul class="list-inline mb-0 font-size-18">
                    <li class="list-inline-item">
                        <a href="#" class="text-muted px-1">
                            <i class="ri-download-2-line"></i>
                        </a>
                    </li>
                    <li class="list-inline-item dropdown">
                        <a class="dropdown-toggle text-muted px-1" href="#" role="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            <i class="ri-more-fill"></i>
                        </a>
                        <div class="dropdown-menu dropdown-menu-end">
                            <a class="dropdown-item direct_message ${is_self?"d-none":"block"}" onclick='onSelectFriend(${member.id})' href="#">Message</a>
                            <a class="dropdown-item" href="${window.location.origin+'/account/profile/'+member.id}">View Profile</a>
                            `
                            // <a class="dropdown-item remove-member" data-removee=${member.id} style="display:${can_kick?"block":"none"}" href="#">Kick</a>
                            +`<a class="dropdown-item remove-member" data-removee=${member.id} href="#">Kick</a>
                            <a class="dropdown-item leave-group"  data-is = ${is_self} href="#">Leave Group</a>
                        </div>
                    </li>
                </ul>
            </div>
        </div>
    </div>`
    d_k();
    function d_k(){
        if(can_kick == false){
            document.querySelector('.remove-member').remove();
        }
    }
    groupActions_event_listener(group_thread_id);
    });
}

}
function groupActions_event_listener(gt_id) {
    var kickContainer = document.querySelectorAll(".remove-member");
    var leaveContainer = document.querySelectorAll(".leave-group");
    [].map.call(kickContainer, function(elem) {
        elem.addEventListener("click",function(){
           let removee_id = this.dataset.removee
        kickMemberFromGroup(removee_id,gt_id);
        }, false);
    });
    [].map.call(leaveContainer, function(elem) {
        if(elem.dataset.is == 'false'){
            elem.remove();
        }
        elem.addEventListener("click",function(){
        leaveGroup(gt_id);
        }, false);
    });
}

function kickMemberFromGroup(removee_id,gt_id){
    var csrftoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    let fd = new FormData();
    fd.append("csrfmiddlewaretoken",csrftoken)
    fd.append("removee_id",parseInt(removee_id))
    fd.append("thread_id",parseInt(gt_id))
    $.ajax({
        type:"POST",
        datatype:"json",
        url:"remove_group_member/",
        data:fd,
        success:(response)=>{
            console.log("kick member from group",response)
        },
        error:(response)=>{
            alert(response);
        },
        cache: false,
        contentType: false,
        processData: false,
    });
}

function leaveGroup(gt_id){
    var csrftoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    let fd = new FormData();
    fd.append("csrfmiddlewaretoken",csrftoken)
    fd.append("thread_id",parseInt(gt_id))
    $.ajax({
        type:"POST",
        datatype:"json",
        url:"leave_group/",
        data:fd,
        success:(response)=>{
            console.log("leave group",response)
        },
        error:(response)=>{
            alert(response);
        },
        cache: false,
        contentType: false,
        processData: false,
    });
    groupChatWebSocket.send(JSON.stringify(
        {
            'command':'leave_group_chat',
        }
    ));
}

var submitbutton = $('#chat_name_change_submit');
$('#gc_name_change_modal').on('hidden.bs.modal', function () {
    $(this).find('form').trigger('reset');
})

$('#chat_name_change_form :input').bind('change keyup', function () {
    var current_chat_name = document.getElementById('topbar_otheruser_name').textContent;
    var disable = true;
    console.log('current chat name',current_chat_name,$(this).val());
    if(current_chat_name == $(this).val()){
        disable = true;
    }else{
        disable = false;
    }
    submitbutton.prop('disabled', disable);
});



$('#chat_name_change_submit').on('click',()=>{
    var csrftoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    const fd = new FormData();
    fd.append('csrfmiddlewaretoken',csrftoken);
    fd.append('thread_id',$('#change_group_name').data('threadid'));
    fd.append('change_group_name',$('#change_group_name').val());
    $.ajax({
        type:"POST",
        datatype:"json",
        url: 'update_group_chat_name/',
        data:fd,
        success: function(response){
            var new_gc_name = response['new_gc_name'];
            if(response['status']=='changed'){
                $('#topbar_otheruser_name').html(new_gc_name);
                $('#chat_name_change_form :input').attr('value',new_gc_name);
                $('#id_other_username').html(new_gc_name);
                $('#chat_change_name_close_btn').click();
            }
        },
        error: function(error){
            console.log(error);
        },
        cache: false,
        contentType: false,
        processData: false,
    })
})


$('#chat_photo_change_submit').on('click',()=>{
    var csrftoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    const fd = new FormData();
    fd.append('csrfmiddlewaretoken',csrftoken);
    fd.append('thread_id',$('#change_group_name').data('threadid'));
    fd.append('change_group_photo',$('#change_gc_photo')[0].files[0]);
    $.ajax({
        type:"POST",
        datatype:"json",
        url: 'update_group_chat_photo/',
        data:fd,
        success: function(response){
            var new_gc_photo = response['new_gc_photo'];
            if(response['status']=='changed'){
                preloadImage(new_gc_photo, 'other_user_profile_image');
                preloadImage(new_gc_photo,'topbar_otheruser_image');
                $('#chat_change_photo_close_btn').click();
                $('#gc_photo_change_form')[0].reset();
            }
        },
        error: function(error){
            console.log(error);
        },
        cache: false,
        contentType: false,
        processData: false,
    })
})