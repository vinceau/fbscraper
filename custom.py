"""This module contains all the Facebook specific selectors and text.
Whenever Facebook modifies their code, this will need to be updated to accomodate the changes. #webscraperlife
"""

"""These are selectors written in css to select different parts of the page
"""
css_selectors = {
    #email and password field used to login
    'email_field': '#email',
    'password_field': '#pass',
    #the login form to submit
    'login_form': '#login_form',
    #the individual photos in the photos page
    'photo_selector': '#pagelet_timeline_medley_photos div.fbPhotoStarGridElement',
}


"""These are selectors written in xpath to select different parts of the page
"""
xpath_selectors = {
    'friends_selector': "//ul[contains(@data-pnref, 'friends')]//div[contains(@class, 'uiProfileBlockContent')]//a[@data-hovercard]",
    'likes_selector': "//div[@id='pagelet_timeline_medley_likes']//li//a[@data-hovercard and not(*)]",
    'user_posts': "//div[contains(@class, 'fbUserContent')]/div[1]",
    'post_date': ".//abbr/span[contains(@class, 'timestampContent')]/..",
    #the header that says things like 'Sorry, this page isn't available'
    #used for checking if the profile is a valid page or not
    'error_header': "//div[@id='content']//h2",
    #the left hand side of the about page with the different sections
    'about_links': "//ul[@data-pnref='about']/li//ul[@data-testid = 'info_section_left_nav']/li",
    #the main about page with all the content of the individual section
    'about_main': "//ul[@data-pnref='about']/li[2]/div/div[2]",
}


"""Query parameters to set the profile to different sections
"""
page_references = {
    'friends_page': 'sk=friends',
    'likes_page': 'sk=likes',
    'photos_page': 'sk=photos',
    'about_page': 'sk=about',
}


"""Specific text used for text matching
"""
text_content = {
    #used for checking if a profile is valid or not
    'error_header_text': 'isn\'t available',
}
