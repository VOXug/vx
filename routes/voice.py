from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from models import db, VoiceModel, AudioClip
from forms.voice import VoiceModelForm, AudioClipForm
from utils.openvoice import train_voice_model, generate_audio

voice_bp = Blueprint('voice', __name__, url_prefix='/voice')

@voice_bp.route('/')
@login_required
def index():
    voice_models = VoiceModel.query.all()
    return render_template('voice/models.html', title='Voice Models', voice_models=voice_models)

@voice_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_voice_model():
    form = VoiceModelForm()
    
    if form.validate_on_submit():
        # Save the uploaded voice sample file
        voice_file = form.voice_file.data
        filename = secure_filename(f"{uuid.uuid4()}_{voice_file.filename}")
        file_path = os.path.join(current_app.config['VOICE_MODELS_FOLDER'], filename)
        voice_file.save(file_path)
        
        # Create a new voice model record
        voice_model = VoiceModel(
            name=form.name.data,
            description=form.description.data,
            file_path=file_path,
            is_active=True
        )
        db.session.add(voice_model)
        db.session.commit()
        
        # Start training the voice model (this would be a Celery task in production)
        flash('Voice model uploaded successfully. Training will begin shortly.', 'success')
        
        # In a real implementation, you would call a Celery task here
        # train_voice_model.delay(voice_model.id)
        
        return redirect(url_for('voice.index'))
    
    return render_template('voice/form.html', title='Add Voice Model', form=form)

@voice_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_voice_model(id):
    voice_model = VoiceModel.query.get_or_404(id)
    form = VoiceModelForm(obj=voice_model)
    
    if form.validate_on_submit():
        voice_model.name = form.name.data
        voice_model.description = form.description.data
        
        if form.voice_file.data:
            # Save the new uploaded voice sample file
            voice_file = form.voice_file.data
            filename = secure_filename(f"{uuid.uuid4()}_{voice_file.filename}")
            file_path = os.path.join(current_app.config['VOICE_MODELS_FOLDER'], filename)
            voice_file.save(file_path)
            
            # Update the file path
            voice_model.file_path = file_path
            
            # In a real implementation, you would call a Celery task here to retrain
            # train_voice_model.delay(voice_model.id)
            flash('Voice model updated successfully. Retraining will begin shortly.', 'success')
        else:
            flash('Voice model updated successfully.', 'success')
        
        db.session.commit()
        return redirect(url_for('voice.index'))
    
    return render_template('voice/form.html', title='Edit Voice Model', form=form, voice_model=voice_model)

@voice_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_voice_model(id):
    voice_model = VoiceModel.query.get_or_404(id)
    
    # Check if the voice model is being used by any audio clips
    if voice_model.audio_clips:
        flash('Cannot delete voice model as it is being used by audio clips.', 'danger')
        return redirect(url_for('voice.index'))
    
    # Delete the voice model file
    if os.path.exists(voice_model.file_path):
        os.remove(voice_model.file_path)
    
    # Delete the sample audio if it exists
    if voice_model.sample_audio_path and os.path.exists(voice_model.sample_audio_path):
        os.remove(voice_model.sample_audio_path)
    
    db.session.delete(voice_model)
    db.session.commit()
    
    flash('Voice model deleted successfully.', 'success')
    return redirect(url_for('voice.index'))

@voice_bp.route('/<int:id>/generate-sample', methods=['POST'])
@login_required
def generate_sample(id):
    voice_model = VoiceModel.query.get_or_404(id)
    
    # Sample text to generate
    sample_text = request.form.get('sample_text', 'Hello, this is a test of the voice model.')
    
    # Generate a sample audio file using the voice model
    # In a real implementation, this would be a Celery task
    # sample_audio_path = generate_audio(voice_model.id, sample_text)
    
    # For now, we'll just simulate it
    sample_filename = f"sample_{uuid.uuid4()}.wav"
    sample_audio_path = os.path.join(current_app.config['AUDIO_FOLDER'], sample_filename)
    
    # Update the voice model with the sample audio path
    voice_model.sample_audio_path = sample_audio_path
    db.session.commit()
    
    flash('Sample audio generated successfully.', 'success')
    return redirect(url_for('voice.index'))

@voice_bp.route('/audio')
@login_required
def audio_clips():
    audio_clips = AudioClip.query.all()
    return render_template('voice/audio_clips.html', title='Audio Clips', audio_clips=audio_clips)

@voice_bp.route('/audio/add', methods=['GET', 'POST'])
@login_required
def add_audio_clip():
    form = AudioClipForm()
    
    # Populate the voice model choices
    form.voice_model_id.choices = [(m.id, m.name) for m in VoiceModel.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        # Generate the audio clip using the selected voice model and text
        # In a real implementation, this would be a Celery task
        # file_path = generate_audio(form.voice_model_id.data, form.text_content.data, form.language_id.data)
        
        # For now, we'll just simulate it
        filename = f"audio_{uuid.uuid4()}.wav"
        file_path = os.path.join(current_app.config['AUDIO_FOLDER'], filename)
        
        # Create a new audio clip record
        audio_clip = AudioClip(
            name=form.name.data,
            file_path=file_path,
            text_content=form.text_content.data,
            flow_step=form.flow_step.data,
            sentiment=form.sentiment.data,
            voice_model_id=form.voice_model_id.data,
            language_id=form.language_id.data
        )
        db.session.add(audio_clip)
        db.session.commit()
        
        flash('Audio clip created successfully.', 'success')
        return redirect(url_for('voice.audio_clips'))
    
    return render_template('voice/audio_form.html', title='Add Audio Clip', form=form)

@voice_bp.route('/audio/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_audio_clip(id):
    audio_clip = AudioClip.query.get_or_404(id)
    form = AudioClipForm(obj=audio_clip)
    
    # Populate the voice model choices
    form.voice_model_id.choices = [(m.id, m.name) for m in VoiceModel.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        audio_clip.name = form.name.data
        audio_clip.text_content = form.text_content.data
        audio_clip.flow_step = form.flow_step.data
        audio_clip.sentiment = form.sentiment.data
        audio_clip.voice_model_id = form.voice_model_id.data
        audio_clip.language_id = form.language_id.data
        
        # If the text content or voice model changed, regenerate the audio
        if (form.text_content.data != audio_clip.text_content or 
            form.voice_model_id.data != audio_clip.voice_model_id or
            form.language_id.data != audio_clip.language_id):
            
            # In a real implementation, this would be a Celery task
            # file_path = generate_audio(form.voice_model_id.data, form.text_content.data, form.language_id.data)
            # audio_clip.file_path = file_path
            
            flash('Audio clip updated successfully. Regeneration will begin shortly.', 'success')
        else:
            flash('Audio clip updated successfully.', 'success')
        
        db.session.commit()
        return redirect(url_for('voice.audio_clips'))
    
    return render_template('voice/audio_form.html', title='Edit Audio Clip', form=form, audio_clip=audio_clip)

@voice_bp.route('/audio/<int:id>/delete', methods=['POST'])
@login_required
def delete_audio_clip(id):
    audio_clip = AudioClip.query.get_or_404(id)
    
    # Delete the audio file
    if os.path.exists(audio_clip.file_path):
        os.remove(audio_clip.file_path)
    
    db.session.delete(audio_clip)
    db.session.commit()
    
    flash('Audio clip deleted successfully.', 'success')
    return redirect(url_for('voice.audio_clips'))

@voice_bp.route('/audio/<int:id>/preview')
@login_required
def preview_audio(id):
    audio_clip = AudioClip.query.get_or_404(id)
    
    # In a real implementation, you would serve the audio file
    # For now, we'll just return a JSON response
    return jsonify({
        'id': audio_clip.id,
        'name': audio_clip.name,
        'file_path': audio_clip.file_path
    })
