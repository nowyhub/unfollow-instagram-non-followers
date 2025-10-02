// Instagram Unfollow Non-Followers Script (ACCURATE VERSION)
// This compares your Following vs Followers lists

(async function() {
    const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
    
    console.log('=== INSTAGRAM UNFOLLOW NON-FOLLOWERS ===');
    console.log('Step 1: Getting your followers list...');
    
    // Get lists via Instagram's internal API
    async function getUserList(endpoint, userId) {
        let users = [];
        let after = null;
        
        do {
            const url = after 
                ? `${endpoint}?count=50&max_id=${after}`
                : `${endpoint}?count=50`;
                
            const res = await fetch(url, {
                headers: {
                    'x-ig-app-id': '936619743392459'
                }
            });
            
            const data = await res.json();
            users.push(...data.users);
            after = data.next_max_id;
            
            console.log(`Loaded ${users.length} users...`);
            await delay(1000);
            
        } while (after);
        
        return users;
    }
    
    // Get current user ID
    const username = window.location.pathname.split('/')[1];
    const userRes = await fetch(`https://www.instagram.com/api/v1/users/web_profile_info/?username=${username}`, {
        headers: { 'x-ig-app-id': '936619743392459' }
    });
    const userData = await userRes.json();
    const userId = userData.data.user.id;
    
    console.log(`Your user ID: ${userId}`);
    
    // Get followers and following
    console.log('Getting followers...');
    const followers = await getUserList(`https://www.instagram.com/api/v1/friendships/${userId}/followers/`, userId);
    
    console.log('Getting following...');
    const following = await getUserList(`https://www.instagram.com/api/v1/friendships/${userId}/following/`, userId);
    
    // Find who doesn't follow back
    const followerIds = new Set(followers.map(u => u.pk));
    const notFollowingBack = following.filter(u => !followerIds.has(u.pk));
    
    console.log(`\n=== RESULTS ===`);
    console.log(`You follow: ${following.length}`);
    console.log(`Follow you: ${followers.length}`);
    console.log(`Don't follow back: ${notFollowingBack.length}`);
    
    if (notFollowingBack.length === 0) {
        console.log('Everyone follows you back! Nothing to do.');
        return;
    }
    
    console.log('\nUsers who don\'t follow back:');
    notFollowingBack.forEach(u => console.log(`- ${u.username}`));
    
    console.log('\n=== STARTING UNFOLLOW PROCESS ===');
    console.log('Waiting 3 seconds...');
    await delay(3000);
    
    let unfollowed = 0;
    
    for (let user of notFollowingBack) {
        try {
            const res = await fetch(`https://www.instagram.com/api/v1/friendships/destroy/${user.pk}/`, {
                method: 'POST',
                headers: {
                    'x-ig-app-id': '936619743392459',
                    'x-csrftoken': document.cookie.match(/csrftoken=([^;]+)/)[1]
                }
            });
            
            if (res.ok) {
                unfollowed++;
                console.log(`✓ Unfollowed ${user.username} (${unfollowed}/${notFollowingBack.length})`);
            } else {
                console.log(`✗ Failed to unfollow ${user.username}`);
            }
            
            // Random delay between 3-6 seconds to avoid detection
            await delay(3000 + Math.random() * 3000);
            
        } catch (e) {
            console.log(`Error unfollowing ${user.username}:`, e);
        }
    }
    
    console.log(`\n=== COMPLETE ===`);
    console.log(`Successfully unfollowed ${unfollowed} users who don't follow you back.`);
    
})();
