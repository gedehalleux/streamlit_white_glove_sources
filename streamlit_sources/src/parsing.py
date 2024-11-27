def get_0_based_pages(human_readable_pages_list, start_page, pages_per_page):
    """
    Convert human-readable pages back to virtual pages.

    Args:
    human_readable_pages_list (list): List of human-readable pages.
    start_page (int): The starting page number.
    pages_per_page (int): Number of pages per virtual page.

    Returns:
    list: List of virtual pages.
    """
    virtual_pages_list = []

    if start_page is not None and pages_per_page is not None:
        for human_page in human_readable_pages_list:
            virtual_page = ((human_page - start_page) // pages_per_page) + 1
            virtual_pages_list.append(virtual_page)
    else:
        virtual_pages_list = [p-1 for p in human_readable_pages_list]  # If no pagination details, assume input is virtual pages
    return virtual_pages_list

def get_human_pages(virtual_pages_list, start_page, pages_per_page):
    human_readable_pages_list = []
    if start_page is not None and pages_per_page is not None:
        for virtual_page in virtual_pages_list:
            human_page = (((virtual_page-1) * pages_per_page) + start_page) - (1 * pages_per_page)
            human_readable_pages_list.append(human_page)
    else: 
        human_readable_pages_list = [v for v in virtual_pages_list]

    return human_readable_pages_list