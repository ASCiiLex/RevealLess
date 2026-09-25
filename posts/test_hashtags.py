from django.urls import reverse
from django.test import TestCase


class HashtagDetailRedirectTests(TestCase):
    def test_redirige_al_feed_react_con_el_hashtag(self):
        response = self.client.get(reverse('hashtag_detail', args=['plottwist']))
        self.assertRedirects(
            response, '/feed/react/?hashtag=plottwist', fetch_redirect_response=False
        )