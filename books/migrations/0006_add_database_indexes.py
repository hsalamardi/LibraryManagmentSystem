# Generated manually for database index optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0005_alter_themeconfiguration_fields'),
    ]

    operations = [
        # Add indexes to Book model
        migrations.AlterField(
            model_name='book',
            name='shelf',
            field=models.CharField(db_index=True, help_text='Shelf location', max_length=20),
        ),
        migrations.AlterField(
            model_name='book',
            name='title',
            field=models.CharField(db_index=True, help_text='Book title', max_length=500),
        ),
        migrations.AlterField(
            model_name='book',
            name='isbn',
            field=models.CharField(blank=True, db_index=True, help_text='ISBN-13 format', max_length=17, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='barcode',
            field=models.CharField(blank=True, db_index=True, help_text='Barcode for scanning', max_length=50, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='author',
            field=models.CharField(db_index=True, help_text='Primary author(s)', max_length=500),
        ),
        migrations.AlterField(
            model_name='book',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('ar', 'Arabic'), ('fr', 'French'), ('es', 'Spanish'), ('de', 'German'), ('other', 'Other')], db_index=True, default='en', max_length=10),
        ),
        migrations.AlterField(
            model_name='book',
            name='dewey_code',
            field=models.CharField(blank=True, db_index=True, help_text='Dewey Decimal Classification', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='main_class',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='is_available',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='date_added',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        
        # Add indexes to Borrower model
        migrations.AlterField(
            model_name='borrower',
            name='borrow_date',
            field=models.DateField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='borrower',
            name='due_date',
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name='borrower',
            name='return_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='borrower',
            name='status',
            field=models.CharField(choices=[('borrowed', 'Borrowed'), ('returned', 'Returned'), ('overdue', 'Overdue'), ('lost', 'Lost')], db_index=True, default='borrowed', max_length=20),
        ),
        migrations.AlterField(
            model_name='borrower',
            name='fine_amount',
            field=models.DecimalField(db_index=True, decimal_places=2, default=0.0, max_digits=10),
        ),
        
        # Add indexes to BookReservation model
        migrations.AlterField(
            model_name='bookreservation',
            name='reservation_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='bookreservation',
            name='expiry_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='bookreservation',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('fulfilled', 'Fulfilled'), ('cancelled', 'Cancelled'), ('expired', 'Expired')], db_index=True, default='active', max_length=20),
        ),
    ]