<template>

    <div class="main_container">

        <div v-for="category in categories" :key="category[0]"> 
            <h2> {{category[1]}} </h2>
            <div class="icon_container">
                <div v-for="item in all_icons(category[0])" 
                    :key="item.id" 
                    @click="item.id === 'Training' ? null : app.functions.switch_page(item.id)" 
                    class="select_app"
                    :class="{ 'select_app_disabled': item.id === 'Training' }"> 
                    <div class="select_app_image" v-bind:style="{ 'background-image': 'url(' +( item.img_icon || default_img )+ ')' }"></div>
                    <div class="select_app_desc"> 
                        <div class="select_app_text">
                            <h2>{{item.text}}</h2> 
                            <p>{{item.description}}</p>
                        </div>
                        <div v-if="item.id === 'Training'" class="l_button button_disabled" style="margin-top: 10px; width: fit-content;"> Coming Soon </div>
                        <div v-else class="l_button button_colored" style="margin-top: 10px; width: fit-content;"> Open </div>
                    </div> 
                </div>
            </div>

            <br> 
        </div>
        <hr>
       

    </div>

    
</template>
<script>
const Home ={
    name: 'Home',
    props: {app:Object, },
    components: {},
    mounted() {

    },
    data() {
        return {

            categories: [
                ["main" , "All AI Tools"],
                ["pages" , "Pages"],
                ["misc" , "Miscellaneous"],
            ]
        };
    },
    methods: {
        all_icons(category){
            let ret = []
            let items = (this.app.all_pages_ready ) ?  this.app.$refs.router.all_applet_items : [];
            for(let item of items){
                if(item.home_category == category)
                    ret.push(item)
            }
            return ret;
        }, 
    },
    computed: {
        

        default_img(){
            return require("../assets/imgs/page_icon_imgs/default1.png")
        }
    }
}

export default Home;
Home.title = "Home"
Home.icon = "home"
Home.home_category = undefined
Home.sidebar_show = "always"
// add this to the always_on_pages to the PagesRouter

</script>
<style>
</style>
<style scoped>

.main_container{
    padding: 20px;
    width: 100%;
    height: 100%;
    overflow: auto;
}

.icon_container{
    display: flex;
   flex-wrap: wrap;
}

.select_app{
    width: 280px;
    height: 250px;
    margin: 5px;
    background-color: var(--sidebar-color);
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    border: 1px solid rgba(255, 255, 255, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.select_app:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    border-color: rgba(255, 255, 255, 0.15);
}

.select_app_image {
    height: 120px;
    width: 100%;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

.select_app_desc {
    padding: 12px 15px;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.select_app_text h2 {
    font-size: 1.1rem;
    margin: 0 0 6px 0;
    font-weight: 600;
}

.select_app_text p {
    font-size: 0.85rem;
    margin: 0;
    opacity: 0.8;
    line-height: 1.25;
}

.select_app_disabled {
    filter: grayscale(100%) opacity(0.5);
    cursor: not-allowed !important;
}

.button_disabled {
    background-color: var(--options-input-bg) !important;
    color: rgba(255, 255, 255, 0.4) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    pointer-events: none;
    cursor: not-allowed;
}

@media only screen and (max-width: 1730px) {
  .select_app {
    width : calc(20% - 10px)
  }
}

@media only screen and (max-width: 1430px) {
  .select_app {
    width : calc(25% - 10px)
  }
}

@media only screen and (max-width: 1200px) {
  .select_app {
    width : calc(33% - 10px)
  }
}


</style>