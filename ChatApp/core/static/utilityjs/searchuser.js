const url = window.location.href
const searchForm = document.getElementById('searchbar')
const searchInput = document.getElementById('search-input')
const resultBox = document.getElementById('results-box')
const contactlist = document.getElementById('contact-list')
const csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value 
const memberAddInput = document.getElementById('new_member_add');
const newgcmemberResultBox = document.getElementById('members-result-box'); 
const updateMemberResultBox = document.getElementById('update-members-result-box');
const group_creation_form  = document.getElementById('group_creation_form');
const group_image = document.getElementById('group_image');

const searchData = (search_query) => {

    var ajaxRequest = $.ajax({
        type: 'POST',
        url: 'search/',
        data: { 
            'csrfmiddlewaretoken':csrf,
            'search_query': search_query,
        },
        success: (result) => {
            const data = result.data
            if(Array.isArray(data)){
                contactlist.classList.add('not-visible');
                resultBox.innerHTML = ''
                data.forEach(user=>{
                    // resultBox.innerHTML+=`
                    //     <a href="../account/profile/${user.pk}">
                    //         <div class="row-5 searchlist">
                    //             <div class="col-lg-4">
                    //                 <img src="${user.profile_image}" class="user-image">
                    //             </div>
                    //             <div class="col-lg-8">
                    //                 <h5>${user.first_name} ${user.last_name}</h>
                    //                 <p class="text font-size-sm">@<u>${user.username}</u></p>
                    //             </div>
                    //         </div>
                    //     </a>
                    //     `

                    resultBox.innerHTML+=  `<ul class="list-unstyled search-user-list">
                        <li>
                            <a href="../account/profile/${user.pk}">
                                <div class="d-flex">                            
                                    <div class="chat-user-img online align-self-center me-3 ms-0">
                                        <img src="${user.profile_image}" class="rounded-circle avatar-sm" alt="">
                                        <!-- <span class="user-status"></span> -->
                                    </div>
            
                                    <div class="flex-1 overflow-hidden">
                                        <h5 class="text-truncate font-size-15 mb-1">${user.first_name} ${user.last_name}</h5>
                                        <p class="chat-user-message text-truncate mb-0">@<u>${user.username}</u></p>
                                    </div>
                                </div>
                            </a>
                        </li>
                    </ul>`
                })
                
            }else{
                if(searchInput.value.length > 0){
                    resultBox.innerHTML = `
                    <div class="row-5 searchlist" style="padding:15px;">
                                <div class="col-lg-8">
                                <b><h5>${data}</h5></b>
                                </div>
                    
                    </div>
                    `;
                    
                }else{
                    resultBox.classList.add('not-visible');
                }
            }
        },
        error: (err) => {
            console.log("This is me "+err)
        } 
    })
    if(ajaxRequest){
        if(search_query.length ==0 ){
            resultBox.classList.add('not-visible')
            contactlist.classList.remove('not-visible');
            ajaxRequest.abort();
        }
    }
}

searchInput.addEventListener('keyup',e => {
    if(resultBox.classList.contains('not-visible')){
        resultBox.classList.remove('not-visible')
    }
    searchData(e.target.value.trim())

})


const addMemberSearch = (search_query,memberResultBox,my_section,t_id) => {

    var memberSearchRequest = $.ajax({
        type: 'POST',
        url: 'add_member_search/',
        data: { 
            'csrfmiddlewaretoken':csrf,
            'search_query': search_query,
            'thread_id':t_id,
        },
        success: (result) => {

            const data = result.data
            if(Array.isArray(data)){
                memberResultBox.innerHTML = ''
                data.forEach(user=>{
                    memberResultBox.innerHTML+=`
                    <ul class ="list-unstyled search-user-list">
                    <li>
                        <label for="add-member-checkbox-${user.pk}" id="add-member-label-id" class="add-member-label">
                            <a class='search-result-member'>
                                <div class="d-flex">
                                
                                    <div class="chat-user-img online align-self-center me-3 ms-0">
                                        <img src="${user.profile_image}" class="user-image">
                                    </div>
                                    <div class="flex-1 overflow-hidden">
                                        <h5 class="text-truncate font-size-15 mb-1">${user.first_name} ${user.last_name}</h5>
                                        <p class="chat-user-message text-truncate mb-0">@<u>${user.username}</u></p>
                                    </div>
                                    <div class="font-size-11">
                                        <input type="checkbox" class="add-member-check" data-userid="${user.pk}" data-full_name='${user.first_name} ${user.last_name}' data-imageurl='${user.profile_image}' id='add-member-checkbox-${user.pk}' name='add-member-checkbox-${user.pk}'>
                                    </div>
                                
                                </div>
                            </a>
                        </label>
                    </li>
                    </ul>
                        `
                })

            var $filterCheckboxes = $('input[type="checkbox"]');
           existing = JSON.parse(localStorage.getItem('val'))|| {};
                        
           members_list = [];
            var getUserCheck = (element)=>{
                element.innerHTML='';
                Object.values(existing).forEach(function(val,i){
                    if(val.checked){
                        members_list.push(val.userid);
                        $(document).find('.add-member-check[id='+val.id+']').prop("checked",val.checked);
                        element.innerHTML+=`
                            <div style="position:relative;" class="col-md-3">
                                <button type="button" onclick="remove_preview(this.parentElement,this)" style="color:grey" class="btn close shadow-none AClass" data-userid="${val.userid}" data-removeId="${val.id}">
                                    <span><i class="ri-close-line"></i></span>
                                </button>
                                <figure>
                                <img src="${val.profile_image}" class="user-image-preview">
                                <figcaption>${val.full_name}</figcaption>
                                </figure>
                            </div>
                            `
                    }
                })
            }
                getUserCheck(my_section);
                  $(".add-member-check").click((event) => {
                  var t = event.target;
                  console.log(t);
                  existing = existing ? (existing) : {};
                  console.log("before add",existing);
                  members_list = [];

                   existing[t.id] = {
                       "id":t.id,
                       "userid":t.dataset.userid,
                       "checked":t.checked,
                       "profile_image":t.dataset.imageurl,
                       "full_name":t.dataset.full_name,
                    };
                    console.log("add garepachi ko existing",existing);
                    localStorage.setItem("val", JSON.stringify(existing));
                    getUserCheck(my_section);
                  });
                
            }else{
                if(memberAddInput.value.length > 0){
                    memberResultBox.innerHTML = `
                    <div class="row-5 searchlist" style="padding:15px;">
                                <div class="col-lg-8">
                                <b><h5>${data}</h5></b>
                                </div>
                    
                    </div>
                    `;
                    
                }else{
                    memberResultBox.classList.add('not-visible');
                }
            }
        },
        error: (err) => {
            console.log("This is me "+err)
        } 
    })
    if(memberSearchRequest){
        if(search_query.length ==0 ){
            memberResultBox.classList.add('not-visible')
            memberSearchRequest.abort();
        }
    }
}

function clearStorage(){
    localStorage.clear();
}
function remove_preview(this_parent_element,this_element){
    $(this_parent_element).remove();
    chk_element_id = this_element.dataset.removeid;
    chk_userid = this_element.dataset.userid;
    members_list = members_list.filter(item => item !== chk_userid)
    chk_element = document.getElementById(chk_element_id)
    if(chk_element!=null){
    chk_element.checked = false;
    var event = new Event('click');
    // Dispatch it.
    chk_element.dispatchEvent(event);
    }else if(chk_element==null){
        existing = existing ? (existing) : {};
        existing[chk_element_id]['checked'] = false;
         localStorage.setItem("val", JSON.stringify(existing));
    }
}

memberAddInput.addEventListener('keyup',e => {
    if(newgcmemberResultBox.classList.contains('not-visible')){
        newgcmemberResultBox.classList.remove('not-visible')
    }
    contacts_preview = document.getElementById('contacts_preview')

    addMemberSearch(e.target.value,newgcmemberResultBox,contacts_preview,t_id=null);

})

document.getElementById('add_member_search').addEventListener('keyup',e => {
    console.log("searching member");
    if(updateMemberResultBox.classList.contains('not-visible')){
        updateMemberResultBox.classList.remove('not-visible');
    }
    tid = $('#change_group_name').data('threadid');
    update_contacts_preview = document.getElementById('update_contacts_preview');
    addMemberSearch(e.target.value,updateMemberResultBox,update_contacts_preview,tid);

});

// const group_create_url = window.location.origin+'/create_group_chat'
group_creation_form.addEventListener('submit',event=>{
    event.preventDefault();

    if(typeof members_list==='undefined' || members_list.length==0){
        alert("Add members to the group.")
    }else{
    console.log("form submitting",group_image.files[0]);
    const form_data = new FormData()
    members_list = members_list.toString();
    form_data.append('csrfmiddlewaretoken',csrf);
    form_data.append('group_name',$('#group_name').val());
    form_data.append('group_description',$('#group_description').val());
    form_data.append('image',group_image.files[0]);
    form_data.append('members_list',members_list);
    members_list = [];

    $.ajax({
        type:'POST',
        url:'create_group_chat/',
        enctype: 'multipart/form-data',
        data:form_data,
        success: function(response){
            console.log(response);
            localStorage.clear();
            newgcmemberResultBox.innerHTML = '';
            contacts_preview.innerHTML = '';
            group_creation_form.reset();
            // fetch('http://localhost:8000/chat/chat_thread_list')
            // .then(response => response.json())
            // .then(data =>{
            //     console.log(data)
            //     update_thread_list_view(data)
            // });
            
        },
        error: function(error){
            console.log(error);
        },
        cache: false,
        contentType: false,
        processData: false,
    });
}
});

var add_member_form = document.getElementById('member_add_form')
add_member_form.addEventListener('submit',event=>{
    event.preventDefault();

    if(typeof members_list==='undefined' || members_list.length==0){
        alert("Add members to the group.")
    }else{
    const member_data = new FormData();
    members_list = members_list.toString();
    member_data.append('csrfmiddlewaretoken',csrf);
    member_data.append('members_list',members_list);
    member_data.append('thread_id',$('#change_group_name').data('threadid'));
    members_list = [];

    $.ajax({
        type:'POST',
        url:'add_new_members/',
        data:member_data,
        success: function(response){
            console.log(response);
            localStorage.clear();
            updateMemberResultBox.innerHTML = '';
            update_contacts_preview.innerHTML = '';
            add_member_form.reset();
        },
        error: function(error){
            console.log(error);
        },
        cache: false,
        contentType: false,
        processData: false,
    });
}
});





