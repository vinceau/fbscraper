"""This module contains all the Facebook specific selectors and text.
Whenever Facebook modifies their code, this will need to be updated to accomodate the changes. #webscraperlife

CSS Selectors have better performance than XPath and should be used in all circumstances UNLESS you cannot select it
properly in CSS. For example: CSS does not contain "parent" selectors (in XPath it's simply "..") nor does it have the
ability to select text-only elements, i.e. elements containing only text and no children elements.
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
    'friends_selector': "ul[data-pnref='friends'] div.uiProfileBlockContent a[data-hovercard]",
    'user_posts': "div.fbUserContent > div:first-of-type",
    #the left hand side of the about page with the different sections
    'about_links': "ul[data-pnref='about'] > li ul[data-testid='info_section_left_nav'] > li",
    #the main about page with all the content of the individual section
    'about_main': "ul[data-pnref='about'] > li:nth-child(2) > div > div:nth-child(2)",
    #used for checking if the profile is a valid page or not
    'error_header': "#content h2",
    #selects the different albums
    'indiv_albums': "#pagelet_timeline_medley_photos table.fbPhotosGrid a.photoTextTitle",
    #once inside an album, select the different photos
    'album_photo': "#fbTimelinePhotosContent div.fbPhotoStarGridElement",
}


"""These are selectors written in xpath to select different parts of the page.
Only use XPath when you can't express it in CSS.
"""
xpath_selectors = {
    'likes_selector': "//div[@id='pagelet_timeline_medley_likes']//li//a[@data-hovercard and not(*)]",
    'post_date': ".//abbr/span[contains(@class, 'timestampContent')]/..",
    #individual groups in the groups page
    'groups': "//div[@id='timeline-medley']//ul/li//a[@data-hovercard and not (*)]",
}


"""Query parameters to set the profile to different sections
"""
page_references = {
    'friends_page': 'sk=friends',
    'likes_page': 'sk=likes',
    'photos_page': 'sk=photos',
    'about_page': 'sk=about',
    'groups_page': 'sk=groups',
    'albums': 'sk=photos_albums',
}


"""Specific text used for text matching
"""
text_content = {
    #used for checking if a profile is valid or not
    'error_header_text': 'isn\'t available',
}
