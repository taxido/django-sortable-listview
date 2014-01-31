import urllib

from django.views.generic import ListView
from django.http import QueryDict


class SortableListView(ListView):
    # Defaults, you probably want to specify these when you subclass
    default_sort_field = 'id'
    allowed_sort_fields = {default_sort_field: {'default_direction': '-',
                                                'verbose_name': 'ID'}}
    sort_parameter = 'sort'  # the get parameter e.g. ?page=1&sort=2
    sort_with_querystring = False
    sort_without_pagination = False
    # End of Defaults

    @property
    def sort(self):
        return self.sort_order + self.sort_field

    @property
    def default_sort_order(self):
        return self.allowed_sort_fields[
            self.default_sort_field]['default_direction']

    @property
    def default_sort(self):
        return self.default_sort_order + self.default_sort_field

    def get(self, request, *args, **kwargs):
        self.sort_order, self.sort_field = self.set_sort(request)
        self.sort_link_list = self.get_sort_link_list(request)
        return super(SortableListView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SortableListView,
                        self).get_context_data(**kwargs)
        context['current_sort_query'] = self.get_sort_string()
        context['sort_link_list'] = self.sort_link_list
        return context

    def get_queryset(self):
        qs = super(SortableListView, self).get_queryset()
        qs = qs.order_by(self.sort)
        return qs

    def set_sort(self, request):
        """
        Take the sort parameter from the get parameters and split it into
        the field and the prefix
        """
        # Look for 'sort' in get request. If not available use default.
        sort_request = request.GET.get(self.sort_parameter, self.default_sort)
        if sort_request.startswith('-'):
            sort_order = '-'
            sort_field = sort_request.split('-')[1]
        else:
            sort_order = ''
            sort_field = sort_request
        # Invalid sort requests fail silently
        if not sort_field in self.allowed_sort_fields:
            sort_order = self.default_sort_order
            sort_field = self.default_sort_field
        return (sort_order, sort_field)

    def get_sort_string(self, sort=None):
        if not sort:
            sort = self.sort
        sort_string = ''
        if not sort == self.default_sort:
            sort_string = self.sort_parameter + '=' + sort
        return sort_string

    def get_next_sort_string(self, field):
        """
        If we're already sorted by the field then the sort query
        returned reverses the sort order.
        """
        # self.sort_field is the currect sort field
        if field == self.sort_field:
            next_sort = self.toggle_sort_order() + field
        else:
            default_order_for_field = \
                self.allowed_sort_fields[field]['default_direction']
            next_sort = default_order_for_field + field
        return self.get_sort_string(next_sort)

    def get_sort_indicator(self, field):
        """
        Returns a sort class for the active sort only. That is, if field is not
        sort_field, then nothing will be returned becaues the sort is not
        active.
        """
        indicator = ''
        if field == self.sort_field:
            indicator = 'sort-asc'
            if self.sort_order == '-':
                indicator = 'sort-desc'
        return indicator

    def toggle_sort_order(self):
        if self.sort_order == '-':
            toggled_sort_order = ''
        if self.sort_order == '':
            toggled_sort_order = '-'
        return toggled_sort_order

    def get_sort_link_list(self, request):
        sort_links = []
        for sort_field in self.allowed_sort_fields:
            sort_link = {
                'attrs': sort_field,
                'path': self.get_basic_sort_link(request, sort_field),
                'indicator': self.get_sort_indicator(sort_field),
                'title': self.allowed_sort_fields[sort_field]['verbose_name']}
            sort_links.append(sort_link)
        return sort_links

    def get_basic_sort_link(self, request, field):
        """
        For default this will obliterate any other query parameters in your url. This is
        often useful. For example, if we're using pagination as well, when we
        re-order we probably want to start back at page 1.

        """
        sort_string = self.get_next_sort_string(field)

        if self.sort_with_querystring:
            query_params = request.GET.copy()
            if sort_string:
                query_params.update(QueryDict(sort_string))
            else:
                if self.sort_parameter in query_params:
                    query_params.pop(self.sort_parameter)
            if self.sort_without_pagination:
                if 'page' in query_params:
                    query_params.pop('page')
            return request.path + '?' + urllib.urlencode(query_params)
        if sort_string:
            return request.path + '?' + sort_string
        else:
            return request.path
