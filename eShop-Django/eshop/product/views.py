from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .filters import ProductsFilter

from .serializers import ProductSerializer, ProductImagesSerializer

from .models import Product, ProductImages

# Create your views here.
@api_view(['GET'])
def get_products(request):
    # Filtering products using Django-Filter
    filterset = ProductsFilter(request.GET, queryset=Product.objects.all().order_by('id'))
    
    count = filterset.qs.count()
    
    # pagination 
    resPerPage = 2
    paginator = PageNumberPagination()
    paginator.page_size = resPerPage
    
    queryset = paginator.paginate_queryset(filterset.qs, request)
    
    # Serializing the filtered products using Django-REST-Framework serializer
    serializer = ProductSerializer(queryset, many=True)
    return Response({
        'count': count,
        'resPerPage': resPerPage,
        'products': serializer.data
        })


@api_view(['GET'])
def get_product(request, pk):

    product = get_object_or_404(Product, id=pk)
    serializer = ProductSerializer(product, many=False)
    return Response({'product': serializer.data})
    
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_product(request):
    
    data = request.data
    
    serializer = ProductSerializer(data=data)
    
    if serializer.is_valid():
        
        product = Product.objects.create(**data, user=request.user)
        
        res = ProductSerializer(product, many=False)
        return Response({'product': res.data})
    else:
        
        return Response(serializer.errors, status=400)
    

@api_view(['POST'])
def upload_product_images(request):
    
    data = request.data
    files = request.FILES.getlist('images')

    images = []
    for file in files:
        image = ProductImages.objects.create(product=Product(data['product']), image=file)
        images.append(image)
        
    serializer = ProductImagesSerializer(images, many=True)
    
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_product(request, pk):
    product = get_object_or_404(Product, id=pk)
    
    # Check if the user is same - todo 
    if product.user != request.user:
        return Response({'error': 'You are not authorized to update this product'}, status=status.HTTP_401_UNAUTHORIZED)
    
    product.name = request.data['name']
    product.price = request.data['price']
    product.description = request.data['description']
    product.brand = request.data['brand']
    product.category = request.data['category']
    product.stock = request.data['stock']
    product.ratings = request.data['ratings']
    
    product.save()
    
    serializer = ProductSerializer(product, many=False)
    return Response({'product': serializer.data})
    
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_product(request, pk):
    product = get_object_or_404(Product, id=pk)
    
    # Check if the user is same - todo
    if product.user != request.user:
        return Response({'error': 'You are not authorized to delete this product'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Deleting images with signals
    args = { "product": pk}
    images = ProductImages.objects.filter(**args)
    for image in images:
        image.delete()
        
    product.delete()
    
    return Response({ 'details': 'Product is deleted' }, status=status.HTTP_204_NO_CONTENT)