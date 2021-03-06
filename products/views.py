from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
# Create your views here.

from .forms import VariationInventoryFormSet
from .mixins import (StaffRequiredMixin,
    # LoginRequiredMixin
                     )
from .models import Product, Variation, Category


class CategoryListView(ListView):
    model = Category
    queryset = Category.objects.all()


class CategoryDetailView(DetailView):
    model = Category

    def get_context_data(self, **kwargs):
        context = super(CategoryDetailView, self).get_context_data(**kwargs)
        obj = self.get_object()
        product_set = obj.product_set.all()
        default_products = obj.default_category.all()
        products = (product_set | default_products).distinct()
        context['products'] = products
        return context


class VariationListView(StaffRequiredMixin, ListView):
    model = Variation
    queryset = Variation.objects.all()

    def get_context_data(self, **kwargs):
        context = super(VariationListView, self).get_context_data()
        context['formset'] = VariationInventoryFormSet(queryset=self.get_queryset())
        return context

    def get_queryset(self, *args, **kwargs):
        product_pk = self.kwargs.get('pk')
        if product_pk:
            product = get_object_or_404(Product, pk=product_pk)
            queryset = Variation.objects.filter(product=product)
            return queryset

    def post(self, request, *args, **kwargs):
        formset = VariationInventoryFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save(commit=False)
            for form in formset:
                new_item = form.save(commit=False)
                # if new_item.title:
                product_pk = self.kwargs.get('pk')
                product = get_object_or_404(Product, pk=product_pk)
                new_item.product = product
                new_item.save()
            messages.success(request, 'Your inventory and pricing has been updated.')
            return redirect('products:products')
        raise Http404


class ProductListView(ListView):
    model = Product
    queryset = Product.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data()
        return context

    def get_queryset(self, *args, **kwargs):
        qs = super(ProductListView, self).get_queryset(*args, **kwargs)
        query = self.request.GET.get('q')
        if query:
            qs = self.model.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
            try:
                qs2 = self.model.objects.filter(
                    Q(price=query)
                )
                qs = (qs | qs2).distinct()
            except:
                pass
        return qs


import random


class ProductDetailView(DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        instance = self.get_object()
        context['related'] = sorted(Product.objects.get_related(instance),
                                    key=lambda x: random.random())
        return context


def product_detail_view_func(request, id):
    # product_instance = get_object_or_404(Product, id=id)  # Product.objects.get(id=id)
    try:
        product_instance = get_object_or_404(Product, id=id)  # Product.objects.get(id=id)
    except Product.DoesNoExist:
        raise Http404
    except:
        raise Http404

    template = 'products/product_detail.html'
    context = {
        'object': product_instance,
    }
    return render(request, template, context)
